"""
Debug tools for T2G_arch. Only active when DEBUG = True (settings.py).

These checks verify that after unloading, all plugin objects are really
gone. How cleanup happens (setting a parent, deleteLater(), SignalTracker,
releasing a reference) is decided by the respective code: the checks only
report WHEN something survives, and give a hint about WHO is holding it.

Output goes through print() instead of logging: deliberately kept separate
from the regular log (also because the phase 2 report only runs after the
plugin logger has already been torn down).

Called on plugin unload (plugin_interface.py, unload()):

  from .settings import DEBUG

  if DEBUG:
      from .common.debug_checks import check_for_leaked_objects
      check_for_leaked_objects()

Background:

Every PyQt object consists of two halves with SEPARATE lifetimes:

 - The Python wrapper is managed by the Python garbage collector
   (refcounting plus cycle collector), like any other Python object.
 - The C++ object behind it is managed by Qt. It dies through the
   parent/child cascade (a destroyed parent QObject deletes its
   registered children too) or through an explicit deleteLater() call.
   Simply releasing the reference is only enough if Python is the sole
   owner (created by Python AND without a parent).

This results in two separate kinds of leaks, matching the two phases of
check_for_leaked_objects():

 - Phase 1 (immediately on call): QObject instances from the plugin
   namespace whose C++ OBJECT is still alive. Cause: no parent in the
   plugin object tree and no deleteLater(). Root leaks are reported;
   objects hanging below a reported root are only counted (they die with
   it).
 - Phase 2 (deferred to the next event loop iteration, i.e. AFTER QGIS
   has torn down the modules): pure PYTHON instances from the plugin code
   that survived the full unload. By this point everything module bound
   (constants, enum members, singletons) is dead; whatever is still alive
   is held from OUTSIDE the plugin: a real leak. The report collapses
   holder chains and groups instances of the same kind together ("also
   keeps N further plugin instances alive").

Reacting to messages:

"DEBUG [P1-QObject] !!! Memory leak: <class> ... no parent" (phase 1):
    The C++ object is still alive. Call deleteLater() in the cleanup of
    the OWNING class, or set a parent from the plugin object tree at
    creation time. Careful with QThreads: stop them first (quit()/wait()),
    then tear down.

"DEBUG [P2-Python] !!!: <class>, held by: ..." (phase 2):
    The hint names the holder. Typical causes:
     - "bound method X.y": a callback/observer is still registered
       (e.g. VTK AddObserver, callback lists), deregister it during
       cleanup.
     - "closure (lambda / inner function)": a lambda/partial that
       captures self is still attached to a long lived signal, use
       SignalTracker (common/signal_tracker.py) or disconnect explicitly.
     - "attribute of X" / "list/dict (...)": a long lived structure
       (registry, cache) was not cleared during cleanup.
    Note: a SINGLE leaked object transitively keeps its whole module
    environment alive (instance -> class -> method globals -> module ->
    imports). Fix the phase 1 roots first, then re-evaluate phase 2.

These tools make no claim to completeness: they are tuned for a low
false positive rate, not for exhaustive detection. An empty report means
no obvious leaks were found.
"""

import enum
import gc
import types
import weakref

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QEvent, QObject, QTimer
from qgis.PyQt.QtWidgets import QApplication

# Module prefix of the plugin (folder name = package name), e.g. "Tachy2GIS_arch."
# same lookup as in logger.py
_NAMESPACE_PREFIX = __name__.split(".")[0] + "."

# Builtin containers that traversal descends into: pure pass-through
# containers (gc.get_referents() yields attribute values directly)
_TRAVERSABLE_CONTAINERS = (dict, list, tuple, set, frozenset, types.CellType)


def _walk_referents(root_obj, on_object, max_depth):
    """BFS over gc.get_referents() starting at root_obj: shared traversal
    scaffold for _assign_survivor_children and _collect_plugin_instances.

    on_object(referent) is called for every newly reached object and
    decides whether the search descends further through this object. The
    policy (what counts, where to stop) therefore lives with the caller;
    the visited set and depth limit exist only once.
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
    """Shared report core for phase 2 and the replacement check.

    Checks on the next event loop iteration (after gc.collect() for
    reference cycles) which of the candidates passed in as weakrefs are
    still alive, and reports survivors via print() with a referrer hint.

    The report collapses like phase 1: survivors that are (transitively)
    held by another survivor are counted towards its root; roots of the
    same kind (same class) are grouped into one line with a counter.

    candidates: list of weakref.ref to the instances to check
    headline: message prefix, e.g. "P2-Python"
    all_clear_message: optional success message when nothing survived
    """

    def _assign_survivor_children(root_obj, root_id, survivors, child_of, max_depth=3):
        """Marks survivors reachable from root_obj via references as its
        children (analogous to the parent cascade in phase 1).

        Descends only through builtin containers, not through foreign
        instances, otherwise the search would wander into the QGIS object
        graph.
        """

        def on_object(referent):
            if id(referent) in survivors:
                # first holder found wins; the children of that child are
                # found by its own traversal
                child_of.setdefault(id(referent), root_id)
                return False
            return isinstance(referent, _TRAVERSABLE_CONTAINERS)

        _walk_referents(root_obj, on_object, max_depth)

    def _referrer_hint(obj, max_hints: int = 3) -> str:
        """Short hint about who still references obj: best guess, not exhaustive."""
        hints = []
        for referrer in gc.get_referrers(obj):
            if isinstance(referrer, types.FrameType):
                continue  # the frame of this report function itself
            if isinstance(referrer, dict):
                # instance __dict__? then the owner is more interesting than the dict.
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
                # classic case: a signal connection/callback holds a bound method
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
        gc.collect()  # clear reference cycles before counting survivors
        # id -> weakref. Deliberately NO strong refs: our own bookkeeping would
        # otherwise show up as a holder in every _referrer_hint(). Survivors are
        # by definition held externally: the weakrefs stay resolvable.
        survivors = {}
        for ref in candidates:
            obj = ref()
            if obj is not None:
                survivors[id(obj)] = ref

        if not survivors:
            if all_clear_message:
                print(all_clear_message)
            return

        # collapse: determine holder relationships among the survivors
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
            return sid  # chain ends at the root; on cycles: first revisit

        root_descendants = {}
        for sid in survivors:
            rid = resolve_root(sid)
            if rid != sid:
                root_descendants[rid] = root_descendants.get(rid, 0) + 1

        # group roots of the same kind; determine the referrer hint only once
        # per class (gc.get_referrers() scans the whole heap)
        grouped = {}  # fullname -> [instances, held children, sample weakref]
        for sid, ref in survivors.items():
            if resolve_root(sid) != sid:
                continue  # counted at its root
            obj = ref()
            if obj is None:
                continue
            entry = grouped.setdefault(_fullname(obj), [0, 0, ref])
            entry[0] += 1
            entry[1] += root_descendants.get(sid, 0)

        for name, (instances, held, sample_ref) in sorted(grouped.items()):
            sample = sample_ref()
            hint = _referrer_hint(sample) if sample is not None else "?"
            # print instead of LOGGER: on unload the plugin logger is already torn down here
            line = f"DEBUG [{headline}] !!! {name}"
            if instances > 1:
                line += f" ({instances} Instanzen)"
            hint_label = "z.B. gehalten von" if instances > 1 else "gehalten von"
            line += f" — {hint_label}: {hint}"
            if held:
                line += f" — hält {held} weitere Plugin-Instanzen am Leben"
            print(line)

    def guarded_report_survivors():
        # safety net: an unhandled exception in a Qt slot can hard crash the
        # application (PyQt calls qFatal), a debug tool must never crash the
        # monitored application itself
        try:
            report_survivors()
        except Exception:
            import traceback
            traceback.print_exc()  # stderr uses backslashreplace: encoding safe

    QTimer.singleShot(0, guarded_report_survivors)


def check_for_leaked_objects():
    """Two phase leak detector: call on plugin unload (see module docstring).

    Phase 1 (immediate, this call): QObjects from the plugin namespace
    (_NAMESPACE_PREFIX) whose C++ object is still alive.
    Phase 2 (deferred, see _schedule_python_leak_report): pure Python
    instances that survive the module teardown.

    Project specific experience, phase 1 leaks typically originate here:
     - QObjects (re)created in _on_project_became_valid()
     - objects parented to iface.mainWindow() or iface.mapCanvas():
       the parent outlives the plugin, so the cascade does NOT clean up
     - widgets reparented via iface.addDockWidget(...)
    In all three cases, deleteLater() is needed in the cleanup of the
    owning class.
    """

    def _schedule_python_leak_report():
        """Phase 2 of the leak detector: pure Python instances (not a QObject).

        At call time (inside unload()) the plugin modules are still in
        sys.modules: module wide objects (enum members, singletons,
        constants) would be false positives. So: only collect weakrefs now;
        the report (_schedule_survivor_report) only runs on the next event
        loop iteration, by then QGIS has removed the modules and everything
        module bound is dead. Whatever is still alive then is kept alive
        from outside the plugin: a real leak. On reloadPlugin() the
        instances of the freshly loaded plugin are not in the snapshot: no
        false positives.
        """
        candidates = []
        for obj in gc.get_objects():
            if isinstance(obj, (QObject, type, enum.Enum)):
                continue  # QObjects: phase 1; classes: not instances; enum members
                # live as long as their module (like the check in
                # _collect_plugin_instances below), not a leak, just noise
            if not type(obj).__module__.startswith(_NAMESPACE_PREFIX):
                continue
            try:
                candidates.append(weakref.ref(obj))
            except TypeError:
                pass  # not weakref capable (e.g. NamedTuple instances)

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

    # schedule phase 2: collect candidates as weakrefs now,
    # report only after the module teardown (next event loop iteration)
    _schedule_python_leak_report()

    # info: gc.get_objects() lists every live python object
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
    """Replacement check: verifies with a delay whether replaced instances really die.

    Call BEFORE replacing, passing the old instances (None entries are fine).
    The snapshot is TRANSITIVE: besides the instances passed in, everything
    plugin owned that is reachable from them is captured too (e.g. Profile ->
    Georef/Digitize/Plan/RotationCoords). The contract is therefore: "this
    instance and all plugin objects hanging off it must die".

        if DEBUG:
            from ..common.debug_checks import check_for_surviving_instances
            check_for_surviving_instances(
                self.transformationGui, self.geoEdit,
                context="T2GArchDockWidget.reload()",
            )
        self.transformationGui = TransformationGui(self)
        ...

    Whatever is still alive after the next event loop iteration is held from
    the outside: typically a signal connection to a QGIS singleton
    (lambda/partial), a registered callback, or a forgotten reference. Such
    zombies are the cause of double firing slots after a project reload.
    """

    def _collect_plugin_instances(root_obj, max_depth=5):
        """Collects root_obj and all pure Python plugin instances reachable
        from it as weakrefs (the transitive part of the snapshot).

        Descends through builtin containers and through plugin instances (to
        capture their sub objects too, e.g. Profile -> Georef/Digitize/Plan).
        Skipped:
         - QObjects: they lead back into the live object tree
           (e.g. controller.dockwidget), which would cause false positives;
           QObject leaks are reported by phase 1 on plugin unload.
         - enum members: they live on their class as long as the module is
           loaded, not a leak on project reload, just noise.
        """
        refs = []

        def collect(obj):
            try:
                refs.append(weakref.ref(obj))
            except TypeError:
                pass  # not weakref capable (e.g. NamedTuple instances)

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
