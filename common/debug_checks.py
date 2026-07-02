"""
Debug-Werkzeuge für T2G_arch — nur aktiv wenn DEBUG = True (settings.py).

Diese Checks prüfen, ob nach dem Entladen alle Objekte des Plugins wirklich
weg sind. Wie aufgeräumt wird (Parent setzen, deleteLater(), SignalTracker,
Referenz loslassen), entscheidet der jeweilige Code — die Checks melden nur,
WENN etwas übrig bleibt, und geben einen Hinweis, WER es festhält.

Ausgabe per print() statt Logging: bewusst vom übrigen Log getrennt.
(auch: der Phase-2-Report läuft erst, nachdem der Plugin-Logger bereits
       abgebaut ist.)

Aufruf beim Plugin-Entladen (plugin_interface.py → unload):

  from .settings import DEBUG

  if DEBUG:
      from .common.debug_checks import check_for_leaked_objects
      check_for_leaked_objects()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hintergrund
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Jedes PyQt-Objekt besteht aus zwei Hälften mit GETRENNTER Lebensdauer:

 - Der Python-Wrapper wird vom Python-Garbage-Collector verwaltet
   (Refcounting + Zyklen-Sammler), wie jedes andere Python-Objekt.
 - Das C++-Objekt dahinter wird von Qt verwaltet. Es stirbt durch die
   Parent-Kind-Kaskade (ein zerstörtes Eltern-QObject löscht seine
   registrierten Kinder mit) oder durch expliziten Abbau via deleteLater().
   "Referenz loslassen" genügt nur, wenn Python alleiniger Besitzer ist
   (von Python erzeugt UND ohne Parent).

Daraus ergeben sich zwei getrennte Leak-Arten — und die zwei Phasen von
check_for_leaked_objects():

 - Phase 1 (sofort beim Aufruf): QObject-Instanzen aus dem Plugin-Namespace,
   deren C++-OBJEKT noch lebt. Ursache: kein Parent im Plugin-Baum und kein
   deleteLater(). Root-Leaks werden gemeldet; Objekte, die unter einem
   gemeldeten Root hängen, werden nur gezählt (sie sterben mit ihm).
 - Phase 2 (verzögert auf die nächste Event-Loop-Iteration, also NACH dem
   Modul-Teardown durch QGIS): reine PYTHON-Instanzen aus dem Plugin-Code,
   die den vollständigen Unload überlebt haben. Zu diesem Zeitpunkt ist
   alles Modul-Gebundene (Konstanten, Enum-Member, Singletons) tot — was
   noch lebt, wird von AUSSERHALB des Plugins festgehalten: ein echtes Leak.
   Der Report kollabiert Halter-Ketten und fasst gleichartige Instanzen
   zusammen ("hält N weitere Plugin-Instanzen am Leben").

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reaktion auf Meldungen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"DEBUG [P1-QObject] !!! Memory leak: <Klasse> ... no parent" (Phase 1):
    Das C++-Objekt lebt noch. Im Cleanup der BESITZENDEN Klasse
    deleteLater() aufrufen oder bei der Erzeugung einen Parent aus dem
    Plugin-Objektbaum setzen. Achtung bei QThreads: erst beenden
    (quit()/wait()), dann abbauen.

"DEBUG [P2-Python] !!!: <Klasse> — gehalten von: ..." (Phase 2):
    Der Hinweis nennt den Halter. Typische Ursachen:
     - "gebundene Methode X.y" → ein Callback/Observer ist noch registriert
       (z.B. VTK AddObserver, Callback-Listen) → beim Cleanup deregistrieren.
     - "Closure (lambda / innere Funktion)" → ein lambda/partial, das self
       einfängt, hängt noch an einem langlebigen Signal → SignalTracker
       verwenden (common/signal_tracker.py) oder explizit disconnecten.
     - "Attribut von X" / "list/dict (...)" → eine langlebige Struktur
       (Registry, Cache) wurde beim Cleanup nicht geleert.
    Hinweis: EIN geleaktes Objekt hält transitiv sein ganzes Modul-Umfeld
    fest (Instanz → Klasse → Methoden-Globals → Modul → Importe). Erst die
    Phase-1-Roots beheben, dann Phase 2 neu bewerten.

Diese Werkzeuge erheben keinen Anspruch auf Vollständigkeit — sie sind auf
niedrige Falsch-Positiv-Rate ausgelegt, nicht auf lückenlose Erkennung.
Ein leerer Report bedeutet: keine offensichtlichen Leaks gefunden.
"""

import enum
import gc
import types
import weakref

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QEvent, QObject, QTimer
from qgis.PyQt.QtWidgets import QApplication

# Modul-Prefix des Plugins (Ordnername = Paketname), z.B. "Tachy2GIS_arch."
# — gleiche Ermittlung wie in logger.py
_NAMESPACE_PREFIX = __name__.split(".")[0] + "."

# Builtin-Container, durch die Traversierungen absteigen — reine
# "Durchgangsstationen" (Attributwerte liefert gc.get_referents() direkt)
_TRAVERSABLE_CONTAINERS = (dict, list, tuple, set, frozenset, types.CellType)


def _walk_referents(root_obj, on_object, max_depth):
    """BFS über gc.get_referents() ab root_obj — gemeinsames Traversierungs-
    Gerüst für _assign_survivor_children und _collect_plugin_instances.

    on_object(referent) wird für jedes erstmals erreichte Objekt gerufen und
    entscheidet, ob die Suche durch dieses Objekt weiter absteigt. Die Policy
    (was zählt, wo wird gestoppt) liegt damit beim Aufrufer; visited-Set und
    Tiefenbegrenzung gibt es nur einmal.
    """
    visited = {id(root_obj)}
    frontier = [root_obj]
    for _ in range(max_depth):
        next_frontier = []
        for holder in frontier:
            for referent in gc.get_referents(holder):
                if id(referent) in visited:
                    continue
                visited.add(id(referent))
                if on_object(referent):
                    next_frontier.append(referent)
        frontier = next_frontier


def _fullname(obj) -> str:
    class_object = obj.__class__
    module_object = class_object.__module__
    if module_object == "builtins":
        return class_object.__qualname__  # avoid outputs like "builtins.str"
    return module_object + "." + class_object.__qualname__


def _schedule_survivor_report(candidates, headline, all_clear_message=None):
    """Gemeinsamer Report-Kern für Phase 2 und den Replacement-Check.

    Prüft auf der nächsten Event-Loop-Iteration (nach gc.collect() für
    Referenzzyklen), welche der als Weakref übergebenen Kandidaten noch
    leben, und meldet Überlebende per print() mit Referrer-Hinweis.

    Der Report kollabiert wie Phase 1: Survivors, die (transitiv) von einem
    anderen Survivor gehalten werden, zählen zu dessen Root; gleichartige
    Roots (gleiche Klasse) werden zu einer Zeile mit Zähler zusammengefasst.

    candidates:        Liste von weakref.ref auf die zu prüfenden Instanzen
    headline:          Meldungs-Präfix, z.B. "P2-Python"
    all_clear_message: optionale Erfolgsmeldung, wenn nichts überlebt hat
    """

    def _assign_survivor_children(root_obj, root_id, survivors, child_of, max_depth=3):
        """Markiert Survivors, die von root_obj aus über Referenzen erreichbar sind,
        als dessen Kinder (analog zur Parent-Kaskade in Phase 1).

        Abgestiegen wird nur durch Builtin-Container — nicht durch fremde
        Instanzen, sonst wandert die Suche in den QGIS-Objektgraphen.
        """

        def on_object(referent):
            if id(referent) in survivors:
                # erster gefundener Halter gewinnt; die Kinder des Kindes
                # findet dessen eigener Durchlauf
                child_of.setdefault(id(referent), root_id)
                return False
            return isinstance(referent, _TRAVERSABLE_CONTAINERS)

        _walk_referents(root_obj, on_object, max_depth)

    def _referrer_hint(obj, max_hints: int = 3) -> str:
        """Kurzer Hinweis, wer obj noch referenziert — beste Vermutung, nicht vollständig."""
        hints = []
        for referrer in gc.get_referrers(obj):
            if isinstance(referrer, types.FrameType):
                continue  # der Frame der Report-Funktion selbst
            if isinstance(referrer, dict):
                # Instanz-__dict__? Dann ist der Besitzer interessanter als das dict.
                owner = next(
                    (o for o in gc.get_referrers(referrer) if getattr(o, "__dict__", None) is referrer),
                    None,
                )
                if isinstance(owner, types.ModuleType):
                    hints.append(f"Modul {owner.__name__}")
                elif owner is not None:
                    hints.append(f"Attribut von {_fullname(owner)}")
                else:
                    keys = ", ".join(repr(k) for k in list(referrer)[:3])
                    hints.append(f"dict [{keys}, …]")
            elif isinstance(referrer, types.MethodType):
                # klassischer Fall: Signal-Connection/Callback hält eine gebundene Methode
                hints.append(f"gebundene Methode {referrer.__func__.__qualname__}")
            elif isinstance(referrer, types.CellType):
                hints.append("Closure (lambda / innere Funktion)")
            elif isinstance(referrer, (list, tuple, set)):
                hints.append(f"{type(referrer).__name__} (len {len(referrer)})")
            else:
                hints.append(_fullname(referrer))
            if len(hints) >= max_hints:
                break
        return "; ".join(hints) if hints else "kein direkter Referrer gefunden (evtl. C-Ebene, z.B. sip/Qt)"

    def report_survivors():
        gc.collect()  # Referenzzyklen abräumen, bevor Überlebende gezählt werden
        # id -> Weakref. Bewusst KEINE Strong-Refs: die eigene Buchhaltung würde
        # sonst in jedem _referrer_hint() als Halter auftauchen. Survivors sind
        # per Definition extern gehalten — die Weakrefs bleiben auflösbar.
        survivors = {}
        for ref in candidates:
            obj = ref()
            if obj is not None:
                survivors[id(obj)] = ref

        if not survivors:
            if all_clear_message:
                print(all_clear_message)
            return

        # Kollabieren: Halter-Beziehungen unter den Survivors bestimmen
        child_of = {}
        for sid, ref in survivors.items():
            obj = ref()
            if obj is not None:
                _assign_survivor_children(obj, sid, survivors, child_of)

        def resolve_root(sid):
            seen = set()
            while sid in child_of and sid not in seen:
                seen.add(sid)
                sid = child_of[sid]
            return sid  # Kette endet beim Root; bei Zyklen: erster Wiederbesuch

        root_descendants = {}
        for sid in survivors:
            rid = resolve_root(sid)
            if rid != sid:
                root_descendants[rid] = root_descendants.get(rid, 0) + 1

        # gleichartige Roots zusammenfassen; Referrer-Hinweis nur einmal pro
        # Klasse ermitteln (gc.get_referrers() durchsucht den ganzen Heap)
        grouped = {}  # fullname -> [Instanzen, gehaltene Kinder, Beispiel-Weakref]
        for sid, ref in survivors.items():
            if resolve_root(sid) != sid:
                continue  # wird beim Root mitgezählt
            obj = ref()
            if obj is None:
                continue
            entry = grouped.setdefault(_fullname(obj), [0, 0, ref])
            entry[0] += 1
            entry[1] += root_descendants.get(sid, 0)

        for name, (instances, held, sample_ref) in sorted(grouped.items()):
            sample = sample_ref()
            hint = _referrer_hint(sample) if sample is not None else "?"
            # print statt LOGGER: beim Unload ist der Plugin-Logger hier schon abgebaut
            line = f"DEBUG [{headline}] !!! {name}"
            if instances > 1:
                line += f" ({instances} Instanzen)"
            hint_label = "z.B. gehalten von" if instances > 1 else "gehalten von"
            line += f" — {hint_label}: {hint}"
            if held:
                line += f" — hält {held} weitere Plugin-Instanzen am Leben"
            print(line)

    def guarded_report_survivors():
        # Schutzschicht: eine unbehandelte Exception in einem Qt-Slot kann die
        # Anwendung hart beenden (PyQt ruft qFatal) — ein Debug-Werkzeug darf
        # die überwachte Anwendung niemals selbst crashen
        try:
            report_survivors()
        except Exception:
            import traceback
            traceback.print_exc()  # stderr nutzt backslashreplace — encodingsicher

    QTimer.singleShot(0, guarded_report_survivors)


def check_for_leaked_objects():
    """Zweiphasiger Leak-Detektor — beim Plugin-Unload aufrufen (siehe Modul-Docstring).

    Phase 1 (sofort, dieser Aufruf): QObjects aus dem Plugin-Namespace
    (_NAMESPACE_PREFIX), deren C++-Objekt noch lebt.
    Phase 2 (verzögert, siehe _schedule_python_leak_report): reine
    Python-Instanzen, die den Modul-Teardown überleben.

    Projektspezifische Erfahrungswerte — hier entstehen Phase-1-Leaks typisch:
     - QObjects, die in _on_project_became_valid() (erneut) erzeugt werden
     - Objekte mit Parent iface.mainWindow() oder iface.mapCanvas():
       der Parent überlebt das Plugin, die Kaskade räumt also NICHT auf
     - Widgets, die via iface.addDockWidget(...) umgeparentet wurden
    In allen drei Fällen braucht es deleteLater() im Cleanup der
    besitzenden Klasse.
    """

    def _schedule_python_leak_report():
        """Phase 2 des Leak-Detektors: reine Python-Instanzen (kein QObject).

        Beim Aufruf (innerhalb von unload()) liegen die Plugin-Module noch in
        sys.modules — modulweite Objekte (Enum-Member, Singletons, Konstanten)
        wären Falsch-Positive. Daher: jetzt nur Weakrefs einsammeln; der Report
        (_schedule_survivor_report) läuft erst auf der nächsten Event-Loop-
        Iteration — dann hat QGIS die Module entfernt und alles Modul-Gebundene
        ist tot. Was dann noch lebt, wird von außerhalb des Plugins am Leben
        gehalten: ein echtes Leak. Beim reloadPlugin() sind die Instanzen des
        neu geladenen Plugins nicht im Snapshot — keine Falsch-Positive.
        """
        candidates = []
        for obj in gc.get_objects():
            if isinstance(obj, (QObject, type)):
                continue  # QObjects deckt Phase 1 ab; Klassen sind keine Instanzen
            if not type(obj).__module__.startswith(_NAMESPACE_PREFIX):
                continue
            try:
                candidates.append(weakref.ref(obj))
            except TypeError:
                pass  # nicht weakref-fähig (z.B. NamedTuple-Instanzen)

        _schedule_survivor_report(
            candidates,
            headline="P2-Python",
            all_clear_message="DEBUG [P2-Python] all clear — keine überlebenden Python-Instanzen, "
                              "Plugin-Namespace vollständig entladen.",
        )

    def leaked_root_id(q_obj):
        """id of the topmost leaked ancestor, or None if q_obj is itself a root."""
        root_id = None
        parent = q_obj.parent()
        while parent is not None:
            if id(parent) in leaked:
                root_id = id(parent)  # keep climbing; last hit wins
            parent = parent.parent()
        return root_id

    # process pending deleteLater() events first, so widgets just scheduled for deletion
    # (e.g. the toolbar from unload() above) are actually gone and not reported as leaks
    QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    gc.collect()

    # Phase 2 vormerken: Kandidaten jetzt als Weakrefs einsammeln,
    # Report erst nach dem Modul-Teardown (nächste Event-Loop-Iteration)
    _schedule_python_leak_report()

    # Info: gc.get_objects() lists every live python object
    # collect all leaked instances of our classes, keyed by id() (no reliance on __hash__/__eq__)
    leaked = {}
    for obj in gc.get_objects():
        if not isinstance(obj, QObject):
            continue

        try:
            name = _fullname(obj)
        except Exception:
            # skip exotic objects that raise on attribute access while probing
            continue

        if not name.startswith(_NAMESPACE_PREFIX):
            # skip objects not originating from our code
            continue

        if sip.isdeleted(obj):
            # detect if C++ object from Qt is already deleted
            # so only pyqt still holds a reference which will be deleted on next garbage collection
            continue

        leaked[id(obj)] = obj

    # if some ancestor is itself one of our leaks
    # (obj is cascade-deleted once that root is deleted)
    # -> so do not report it but count it to parent
    roots_of_leaked = {}
    for key, obj in leaked.items():
        root_id = leaked_root_id(obj)
        if root_id is None:  # obj is a root
            roots_of_leaked.setdefault(key, (obj, 0))
        else:
            # get root_obj, rcount or set default
            root_obj, rcount = roots_of_leaked.setdefault(root_id, (leaked[root_id], 0))
            roots_of_leaked[root_id] = (root_obj, rcount + 1)

    if not roots_of_leaked:
        print("DEBUG [P1-QObject] all clear — no leaked QObjects, all plugin instances were properly cleaned up.")
        return

    # report only the top level of registered ancestors
    for obj, count in roots_of_leaked.values():
        parent = obj.parent()
        if parent is None:
            note = "no parent"
        else:
            note = f"a parent that is not to be deleted (registered parent: {parent})"

        print(
            f"DEBUG [P1-QObject] !!! Memory leak: {_fullname(obj)} "
            f"C++ object not deleted because it has {note}. "
            f"Call deleteLater() or set a parent! "
            f"It has {count} leaked descendants."
        )


def check_for_surviving_instances(*instances, context: str = ""):
    """Replacement-Check: prüft verzögert, ob ersetzte Instanzen wirklich sterben.

    VOR dem Ersetzen mit den alten Instanzen aufrufen (None-Einträge sind ok).
    Der Snapshot ist TRANSITIV: Neben den übergebenen Instanzen wird alles
    Plugin-Eigene erfasst, das von ihnen aus erreichbar ist (z.B. Profile →
    Georef/Digitize/Plan/RotationCoords). Der Vertrag lautet also: "diese
    Instanz und alle daran hängenden Plugin-Objekte müssen sterben".

        if DEBUG:
            from ..common.debug_checks import check_for_surviving_instances
            check_for_surviving_instances(
                self.transformationGui, self.geoEdit,
                context="T2GArchDockWidget.reload()",
            )
        self.transformationGui = TransformationGui(self)
        ...

    Was nach der nächsten Event-Loop-Iteration noch lebt, wird von außen
    festgehalten — typisch eine Signal-Verbindung zu einem QGIS-Singleton
    (lambda/partial), ein registrierter Callback oder eine vergessene
    Referenz. Solche Zombies sind die Ursache doppelt feuernder Slots nach
    einem Projekt-Reload.
    """

    def _collect_plugin_instances(root_obj, max_depth=5):
        """Sammelt root_obj und alle von dort erreichbaren reinen Python-Plugin-
        Instanzen als Weakrefs (der transitive Teil des Snapshots).

        Abgestiegen wird durch Builtin-Container und durch Plugin-Instanzen (um
        deren Unterobjekte zu erfassen, z.B. Profile → Georef/Digitize/Plan).
        Übersprungen werden:
         - QObjects: über sie führt der Weg zurück in den lebenden Objektbaum
           (z.B. controller.dockwidget) — das gäbe Falsch-Positive; QObject-Leaks
           meldet Phase 1 beim Plugin-Unload.
         - Enum-Member: sie leben an ihrer Klasse, solange das Modul geladen ist —
           beim Projekt-Reload kein Leak, nur Rauschen.
        """
        refs = []

        def collect(obj):
            try:
                refs.append(weakref.ref(obj))
            except TypeError:
                pass  # nicht weakref-fähig (z.B. NamedTuple-Instanzen)

        def on_object(referent):
            if isinstance(referent, (QObject, type, types.ModuleType, enum.Enum)):
                return False
            if type(referent).__module__.startswith(_NAMESPACE_PREFIX):
                collect(referent)
                return True
            return isinstance(referent, _TRAVERSABLE_CONTAINERS)

        collect(root_obj)
        _walk_referents(root_obj, on_object, max_depth)
        return refs

    snapshot = []
    for obj in instances:
        if obj is not None:
            snapshot.extend(_collect_plugin_instances(obj))
    headline = f"Replace {context}" if context else "Replace"
    _schedule_survivor_report(snapshot, headline, all_clear_message=f"DEBUG [{headline}] all clear.")
