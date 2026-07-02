"""
SignalTracker — optionales Hilfsmittel, um Signal-Verbindungen gesammelt
und deterministisch wieder zu trennen.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hintergrund: Warum ist das in PyQt überhaupt ein Thema?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Jedes PyQt-Objekt besteht aus zwei Hälften: dem Python-Objekt (verwaltet vom
Python-Garbage-Collector) und einem C++-Objekt dahinter (verwaltet von Qt,
siehe common/debug_checks.py). Für Signal-Verbindungen folgt daraus:

 - Qt trennt eine Verbindung automatisch, sobald Sender ODER Empfänger
   (C++-seitig) zerstört wird.
 - PyQt referenziert Slots, die gebundene Methoden sind (self.on_xyz), nur
   SCHWACH: Stirbt das Empfänger-Objekt, löst PyQt die Verbindung von selbst.
   Ein "roher" .connect() auf eine Methode ist deshalb meist unkritisch —
   solange das Objekt sterben darf.

 - Kritisch sind zwei Konstellationen:

   1. Der SENDER ist langlebig (iface, QgsProject.instance(), mapCanvas()):
      Diese QGIS-Singletons überleben jeden Plugin- und Projekt-Reload. Das
      Aufräumen hängt dann allein davon ab, dass der Empfänger stirbt. Hält
      irgendetwas die alte Instanz fest, feuert ihr Slot weiter — nach einem
      Reload zusätzlich zum Slot der neuen Instanz (Doppel-Feuern).

   2. Der SLOT ist ein lambda oder functools.partial: Solche Callables hält
      das Signal STARK. Fängt das lambda `self` ein, entsteht ein Zyklus über
      die C++-Ebene, den Pythons GC nicht sehen kann: Das Signal hält das
      lambda, das lambda hält die Instanz — sie kann nie sterben, die
      Verbindung feuert für immer.

   Veraltete Verbindungen sind nicht nur ein Speicherproblem: Feuert ein
   Slot in ein bereits zerstörtes Objekt, wirft er eine Exception — und
   unbehandelte Exceptions in Slots können die gesamte Anwendung hart
   beenden (PyQt ruft dann qFatal auf, QGIS stürzt ab).

Ob die Objekte des Plugins wirklich sterben, überwachen die Leak-Checks in
common/debug_checks.py. Der SignalTracker ist das Werkzeug, mit dem man dort
gemeldete Fälle deterministisch behebt — oder von vornherein vermeidet.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Wann einsetzen? (Empfehlung, kein Zwang)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 - Die eigene Instanz wird zur Laufzeit ersetzt (z.B. die Modul-Controller
   beim Projekt-Reload in T2GArchDockWidget.reload()) UND verbindet sich mit
   langlebigen QGIS-Signalen.
 - lambdas / functools.partial werden als Slots verbunden.
 - Verbindungen sollen zu einem definierten Zeitpunkt garantiert weg sein.

NICHT nötig, wenn Sender und Empfänger ohnehin dieselbe Lebensdauer haben —
z.B. self.btn.clicked.connect(self.on_click) in einem Widget: Der Button ist
Qt-Kind des Widgets, stirbt mit ihm, und Qt trennt die Verbindung dabei selbst.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Anwendungsbeispiele
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1) QWidget/QObject als Besitzer — vollautomatisches Aufräumen:

    class MyDockWidget(QDockWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._tracker = SignalTracker(disconnect_on_destroyed=self)
            self._tracker.track_connect(
                QgsProject.instance().readProject, self.onProjectRead
            )

    # Stirbt das Widget (Parent-Kaskade oder deleteLater()), feuert Qt sein
    # destroyed-Signal und der Tracker trennt alle Verbindungen von selbst.

2) Reine Python-Klasse als Besitzer — expliziter Aufruf:

    class GeoEdit:
        def setup(self):
            self._tracker = SignalTracker()
            self._tracker.track_connect(iface.mapCanvas().mapToolSet, self.onToolSet)

        def disconnectSignals(self):
            self._tracker.disconnect_all()

    # Wer die Instanz ersetzt, ruft vorher disconnectSignals() auf
    # (siehe T2GArchDockWidget.reload()).

3) lambda-Slot entschärfen:

    self._tracker.track_connect(some_signal, lambda: self.refresh(force=True))

    # Ohne Tracker hielte das Signal das lambda (und damit self) für immer.
    # disconnect_all() durchbricht den Zyklus.
"""

import types
import weakref

from qgis.PyQt.QtCore import QObject


class SignalTracker:
    """Sammelt Signal-Verbindungen, um sie mit disconnect_all() gemeinsam zu trennen.

    Args:
        disconnect_on_destroyed: Optionaler QObject-Besitzer. Dessen destroyed-
            Signal (feuert beim Abbau des C++-Objekts) löst disconnect_all()
            automatisch aus — kein manueller Cleanup-Aufruf nötig.
            Voraussetzung: Der Besitzer stirbt tatsächlich (Parent-Kaskade oder
            deleteLater()); ob das passiert, zeigen die Leak-Checks in
            common/debug_checks.py.
    """

    def __init__(self, disconnect_on_destroyed: QObject | None = None):
        self._connections = []
        if disconnect_on_destroyed is not None:
            # PyQt hält die gebundene Methode schwach: Diese Verbindung hält
            # weder den Tracker noch den Besitzer künstlich am Leben.
            disconnect_on_destroyed.destroyed.connect(self.disconnect_all)

    def track_connect(self, signal, slot):
        """Verbindet signal mit slot und merkt sich das Paar für disconnect_all()."""
        signal.connect(slot)
        if isinstance(slot, types.MethodType):
            # Gebundene Methoden nur schwach merken: Der Tracker darf den
            # Empfänger nicht selbst am Leben halten (das wäre genau das Leak,
            # das er verhindern soll). Stirbt der Empfänger vorher, hat PyQt
            # die Verbindung ohnehin schon getrennt.
            self._connections.append((signal, weakref.WeakMethod(slot)))
        else:
            # lambdas/partials/Funktionen: starke Referenz nötig — für
            # disconnect() wird später dasselbe Objekt gebraucht.
            self._connections.append((signal, slot))

    def disconnect_all(self):
        """Trennt alle gemerkten Verbindungen. Idempotent — Mehrfachaufruf ist ok."""
        for signal, slot_or_ref in self._connections:
            slot = slot_or_ref() if isinstance(slot_or_ref, weakref.WeakMethod) else slot_or_ref
            if slot is None:
                continue  # Empfänger bereits tot → PyQt hat schon getrennt
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass  # Verbindung existiert nicht mehr (z.B. Sender bereits zerstört)
        self._connections.clear()
