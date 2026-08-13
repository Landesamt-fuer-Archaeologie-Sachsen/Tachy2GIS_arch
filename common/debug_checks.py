"""
Debug tools for T2G_arch. Only active when DEBUG = True (settings.py).

These checks verify that after unloading, all plugin objects are really
gone. How cleanup happens (setting a parent, deleteLater(), SignalTracker,
releasing a reference) is decided by the respective code: the checks only
report WHEN something survives, and give a hint about WHO is holding it.

Output goes through print() instead of logging: deliberately kept separate
from the regular log (also because the phase 2 and 3 reports only run
after the plugin logger has already been torn down).

Wiring (plugin_interface.py):

  from .settings import DEBUG

  # in __init__, as the first statement of the plugin's lifetime:
  if DEBUG:
      from .common.debug_checks import install_origin_tracker
      install_origin_tracker()

  # in unload():
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

This results in four kinds of leaks, matching the four phases of
check_for_leaked_objects():

 - Phase 1 (immediately on call): QObject instances from the plugin
   namespace whose C++ OBJECT is still alive. Cause: no parent in the
   plugin object tree and no deleteLater(). Root leaks are reported;
   objects hanging below a reported root are only counted (they die with
   it).
 - Phase 1b (immediately after phase 1): Qt-side sweep of the long-lived
   anchors (main window, map canvas + its scene, project instance, layer
   tree view, top-level widgets). Finds orphans whose Python wrapper died
   and leftovers of EARLIER sessions, both invisible to phases 1/3.
   Caveat learned from the RasterLayerView case: a C++-side reparenting
   alone does not make a leak - if sip ownership stayed with Python, the
   C++ object dies with its wrapper, and only an external reference (a
   console variable, a debugger traceback) turns it into one.
 - Phase 2 (deferred to the next event loop iteration, i.e. AFTER QGIS
   has torn down the modules): pure PYTHON instances from the plugin code
   that survived the full unload. By this point everything module bound
   (constants, enum members, singletons) is dead; whatever is still alive
   is held from OUTSIDE the plugin: a real leak. The report collapses
   holder chains and groups instances of the same kind together.
 - Phase 3 (deferred like phase 2, but for deleteLater() cascades, not
   module teardown): instances of FOREIGN classes (QShortcut, QAction,
   QgsSnappingUtils, ...) that OUR code parented to something long lived.
   Phases 1 and 2 filter by plugin namespace and are structurally blind
   to these. The _OriginTracker records every such parenting live
   (application wide ChildAdded filter plus a look at the Python stack)
   together with the CREATION SITE, so the report can name the exact
   plugin line. Requires install_origin_tracker() at plugin load.

Reacting to messages:

"DEBUG [P1-QObject] !!! Memory leak: <class> ... no parent" (phase 1):
    The C++ object is still alive. Call deleteLater() in the cleanup of
    the OWNING class, or set a parent from the plugin object tree at
    creation time. Careful with QThreads: stop them first (quit()/wait()),
    then tear down.

"DEBUG [P1b-Anchor] !!! <class> hängt noch an <anchor>" (phase 1b):
    An orphan phase 1 cannot see: the Python wrapper is gone or the object
    stems from an earlier session, but the C++ side still hangs on a QGIS
    anchor. Same fix as phase 1, in the owning class's cleanup. If it only
    shows up while a console variable or debugger pins a reference, check
    sip ownership first: a Python-owned widget dies with its wrapper and
    is then a fragility, not a leak.

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

"DEBUG [P3-Origin] !!! <class> — erzeugt in <file:line> — hängt an ..." (phase 3):
    Our code created this foreign-class object at the given line and
    parented it to something that outlives the plugin (typically
    iface.mapCanvas() or mainWindow()). deleteLater() it in the owning
    class's cleanup, or parent it to a plugin object so the cascade takes
    it.
    "kollabiert: N Objekte hängen unter <plugin class>": those die with
    that phase 1 leak, fix the phase 1 root first, then re-run.
    KNOWN NOISE: lines whose creation site merely TRIGGERED QGIS-side
    construction (message log panel building itself during a logMessage
    call, QWindow instances from addDockWidget, legend nodes from layer
    refreshes) describe objects owned by QGIS: the Python stack cannot
    see the C++ frames in between, so plugin code gets the blame. Judge
    by whether the named line actually CONSTRUCTS the reported class.

These tools make no claim to completeness: they are tuned for a low
false positive rate, not for exhaustive detection. An empty report means
no obvious leaks were found.
"""

import enum
import gc
import os
import sys
import traceback
import types
import weakref

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QChildEvent, QEvent, QObject, QTimer
from qgis.PyQt.QtWidgets import QApplication

# Module prefix of the plugin (folder name = package name), e.g. "Tachy2GIS_arch."
# same lookup as in logger.py
_NAMESPACE_PREFIX = __name__.split(".")[0] + "."

# Plugin root directory (this file lives in common/), used to recognise our own
# stack frames in phase 3. Deliberately NOT realpath(): with a symlinked plugin
# install, frame co_filename entries contain the symlink path (as imported),
# and resolving it here would make the prefix match fail silently.
# normcase(): co_filename entries from QGIS's import machinery contain MIXED
# path separators (e.g. "C:\\Users/micha/..."), and a naive startswith would
# fail on the first "/". normcase also folds character case, which Windows
# paths require anyway.
_PLUGIN_DIR = os.path.normcase(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_THIS_FILE = os.path.normcase(os.path.basename(__file__))

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
        # a deleteLater() scheduled from a nested event loop (e.g. the modal
        # plugin manager dialog) may not have been processed yet when this
        # deferred report fires - force it, otherwise wrappers whose C++ death
        # is still pending show up as false survivors
        QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
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


def _plugin_origin():
    """Innermost stack frame from plugin code, or None if the caller is not ours.

    Uses sys._getframe() rather than traceback.extract_stack(): this runs on
    every ChildAdded in the whole application, so walking frames lazily and
    stopping at the first hit is much cheaper than formatting a full stack.
    """
    frame = sys._getframe(1)
    while frame is not None:
        filename = os.path.normcase(frame.f_code.co_filename)
        if filename.startswith(_PLUGIN_DIR) and os.path.basename(filename) != _THIS_FILE:
            # relpath against the original (non-normcased) name would work too,
            # but ntpath.relpath normcases internally, so this stays readable
            return f"{os.path.relpath(frame.f_code.co_filename, _PLUGIN_DIR)}:{frame.f_lineno} in {frame.f_code.co_name}"
        frame = frame.f_back
    return None


class _OriginTracker(QObject):
    """Phase 3 groundwork: records WHERE plugin code parented a QObject.

    Phases 1 and 2 only look at classes from the plugin namespace, so a leaked
    QShortcut/QAction/QgsMapTool (foreign class, but OUR instance) stays
    invisible to them. This tracker closes that gap without requiring
    developers to mark anything: Qt sends ChildAdded to the parent whenever any
    QObject gets one, these events pass through QCoreApplication::notify, and an
    event filter on QApplication therefore sees every parenting in the process.
    The Python stack at that moment says whether our code caused it.

    Only primitive data is stored per record: C++ addresses as ints and the
    creation site as a string. The wrapper handed out by event.child() must NOT
    be kept: at ChildAdded time the C++ pointer is not yet in sip's
    address->wrapper table (the derived constructor has not run yet), so sip
    builds a throwaway QObject wrapper. The correctly typed wrapper is fetched
    at report time via parent.children().

    Parent liveness comes EXCLUSIVELY from Qt's destroyed() signal (fires in
    every ~QObject). sip.isdeleted() on a wrapper captured at ChildAdded time
    is not trustworthy: for objects with a second, owning wrapper (e.g.
    layer.clone() results) the C++ side can die without our wrapper being
    marked, isdeleted() then returns False for freed memory and the next method
    call hard crashes QGIS with an access violation.

    ChildRemoved (Qt sends it on destruction too) drops child records again,
    which keeps the map small and prevents false positives from address reuse.
    """

    def __init__(self):
        super().__init__()
        self.records = {}  # child C++ address -> (parent C++ address, creation site)
        self.parents = {}  # parent C++ address -> wrapper (weakref for own classes, strong otherwise)
        self.dead_parents = set()  # parent addresses whose destroyed() has fired

    def _mark_parent_dead(self, parent=None):
        try:
            if parent is not None:
                self.dead_parents.add(sip.unwrapinstance(parent))
        except Exception:
            pass  # bookkeeping must never crash the destructor that called us

    def eventFilter(self, watched, event):
        # an unhandled exception in an event filter makes PyQt call qFatal,
        # which hard crashes QGIS: never let one escape
        try:
            event_type = event.type()
            if event_type == QEvent.ChildAdded:
                origin = _plugin_origin()
                if origin is not None:
                    parent_address = sip.unwrapinstance(watched)
                    if parent_address in self.dead_parents:
                        # address reused by a new object: the old parent and all
                        # its recorded children are gone for good
                        self.dead_parents.discard(parent_address)
                        self.parents.pop(parent_address, None)
                        self.records = {
                            addr: rec for addr, rec in self.records.items() if rec[0] != parent_address
                        }
                    if parent_address not in self.parents:
                        if _fullname(watched).startswith(_NAMESPACE_PREFIX):
                            # own classes: PyQt pins these wrappers while the C++
                            # object lives, so a weakref suffices. A strong ref
                            # would show up as a false holder in phase 2.
                            try:
                                handle = weakref.ref(watched)
                            except TypeError:
                                handle = None  # not weakref capable: cannot verify later
                        else:
                            # foreign classes (mapCanvas, mainWindow, QMenu, ...):
                            # their wrappers are NOT pinned, a weakref dies as soon
                            # as no Python code holds the wrapper anymore. Keep the
                            # wrapper itself: this owns only the tiny Python
                            # wrapper, never the C++ object, and phase 2 ignores
                            # foreign classes.
                            handle = watched
                        if handle is not None:
                            self.parents[parent_address] = handle
                            # authoritative liveness source, see class docstring
                            watched.destroyed.connect(self._mark_parent_dead)
                    if parent_address in self.parents:
                        # sip.cast: under heavy event traffic sip can hand out a
                        # STALE wrapper cached for a previous event at the same
                        # address (e.g. typed QCloseEvent) which lacks .child();
                        # casting by address gets the correctly typed view
                        child = sip.cast(event, QChildEvent).child()
                        self.records[sip.unwrapinstance(child)] = (parent_address, origin)
            elif event_type == QEvent.ChildRemoved:
                child = sip.cast(event, QChildEvent).child()
                self.records.pop(sip.unwrapinstance(child), None)
        except Exception:
            traceback.print_exc()
        return False  # never consume the event


_origin_tracker = None


def install_origin_tracker():
    """Starts phase 3 recording. Call once on plugin load (see plugin_interface.py).

    Cost: the filter is invoked for EVERY event in the application and every
    ChildAdded walks the Python stack. Hence DEBUG only.
    """
    global _origin_tracker
    if _origin_tracker is not None:
        return
    _origin_tracker = _OriginTracker()
    QApplication.instance().installEventFilter(_origin_tracker)


def _shutdown_origin_tracker():
    """Stops recording and hands the tracker over to the phase 3 report.

    The event FILTER must not survive unload: it sits on QApplication and would
    keep calling into a torn down module namespace on every event in QGIS. The
    tracker OBJECT however stays alive until the deferred report has run: its
    destroyed() connections keep marking parents that die between now and the
    report (deleteLater cascades, module teardown), which is exactly what makes
    the liveness data trustworthy at report time. The report deletes it
    afterwards; if that ever fails, phase 1 of the NEXT unload reports
    _OriginTracker: the tool checks itself here.
    """
    global _origin_tracker
    if _origin_tracker is None:
        return None
    QApplication.instance().removeEventFilter(_origin_tracker)
    tracker = _origin_tracker
    _origin_tracker = None
    return tracker


def _schedule_tracked_qobject_report(tracker):
    """Phase 3 report: objects our code parented to something that is still alive.

    Deferred like phase 2, but for a different reason: not to wait for the
    module teardown (irrelevant here, liveness comes from destroyed()
    bookkeeping), but so pending deleteLater() cascades are through. A single
    sendPostedEvents() pass misses deletions that are only scheduled while it
    runs.

    Survivors whose ancestor chain contains another survivor or a live plugin
    namespace QObject (a phase 1 leak root such as a forgotten dialog) die with
    that root's fix and are only counted, not listed: without this, ONE leaked
    dialog floods the report with dozens of lines for its menus and buttons.
    """
    if tracker is None:
        return

    def report():
        # same rationale as in report_survivors(): flush pending deferred
        # deletions before judging liveness
        QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        gc.collect()

        # pass 1: which recorded children are still alive under their recorded
        # parent? Parents are only touched if destroyed() has NOT fired.
        survivors = {}  # child C++ address -> (child wrapper, parent wrapper, origin)
        children_cache = {}
        for child_address, (parent_address, origin) in tracker.records.items():
            if parent_address in tracker.dead_parents:
                continue  # parent destroyed (authoritative): child died with it
            handle = tracker.parents.get(parent_address)
            parent = handle() if isinstance(handle, weakref.ref) else handle
            if parent is None or sip.isdeleted(parent):
                continue
            key = id(parent)
            if key not in children_cache:
                # correctly typed wrappers, unlike the ones seen at ChildAdded time
                children_cache[key] = {
                    sip.unwrapinstance(child): child
                    for child in parent.children()
                    if not sip.isdeleted(child)
                }
            child = children_cache[key].get(child_address)
            if child is None:
                continue  # no longer a child of that parent: cleaned up properly
            survivors[child_address] = (child, parent, origin)

        if not survivors:
            print("DEBUG [P3-Origin] all clear — keine von uns erzeugten Fremd-QObjects überlebt.")
            return

        # pass 2: collapse like phase 1. Walking the ancestor chain of a LIVE
        # child is safe: Qt destroys children before their parent, so every
        # ancestor of a living object is alive.
        def collapse_target(child):
            """(kind, key) of the TOPMOST reportable ancestor, or None for a root.

            Taking the topmost hit (like phase 1's leaked_root_id) makes the
            resolution transitive without chain bookkeeping: everything below a
            leaked dialog lands directly in that dialog's bucket.
            """

            target = None
            # QObject.parent(x) instead of x.parent(): some classes shadow the
            # no-arg QObject method with their own overload (e.g.
            # QAbstractItemModel.parent(child: QModelIndex)) which then raises
            # TypeError when called without arguments
            parent = QObject.parent(child)
            while parent is not None and not sip.isdeleted(parent):
                try:
                    parent_address = sip.unwrapinstance(parent)
                    parent_name = _fullname(parent)
                except Exception:
                    break  # exotic wrapper: stop climbing, keep what we have
                if parent_address in survivors:
                    target = ("record", parent_address)
                elif parent_name.startswith(_NAMESPACE_PREFIX):
                    target = ("plugin", (parent_name, parent_address))
                parent = QObject.parent(parent)
            return target

        descendants = {}   # root address -> collapsed records below it
        plugin_roots = {}  # (plugin fullname, address) -> collapsed records below it
        roots = []
        for child_address, (child, parent, origin) in survivors.items():
            target = collapse_target(child)
            if target is None:
                roots.append(child_address)
            elif target[0] == "record":
                descendants[target[1]] = descendants.get(target[1], 0) + 1
            else:
                plugin_roots[target[1]] = plugin_roots.get(target[1], 0) + 1

        grouped = {}  # (child class, parent class, creation site) -> [instances, held]
        for child_address in roots:
            child, parent, origin = survivors[child_address]
            try:
                grouped_key = (_fullname(child), _fullname(parent), origin)
            except Exception:
                continue  # exotic wrapper raising on probing: nothing useful to report
            entry = grouped.setdefault(grouped_key, [0, 0])
            entry[0] += 1
            entry[1] += descendants.get(child_address, 0)

        for (child_name, parent_name, origin), (count, held) in sorted(grouped.items()):
            line = f"DEBUG [P3-Origin] !!! {child_name}"
            if count > 1:
                line += f" ({count} Instanzen)"
            line += f" — erzeugt in {origin} — hängt an {parent_name}"
            if held:
                line += f" — darunter {held} weitere erfasste Objekte"
            print(line)

        # one summary line per phase 1 leak root instead of listing its children
        plugin_grouped = {}  # fullname -> [root instances, collapsed records]
        for (fullname, _address), held in plugin_roots.items():
            entry = plugin_grouped.setdefault(fullname, [0, 0])
            entry[0] += 1
            entry[1] += held
        for fullname, (instances, held) in sorted(plugin_grouped.items()):
            line = f"DEBUG [P3-Origin] kollabiert: {held} erfasste Objekte hängen unter {fullname}"
            if instances > 1:
                line += f" ({instances} Instanzen)"
            line += " — Phase-1-Leak, sie sterben mit dessen Fix"
            print(line)

    def guarded_report():
        try:
            report()
        except Exception:
            traceback.print_exc()
        finally:
            # only now: the destroyed() bookkeeping had to stay live until here
            tracker.deleteLater()

    QTimer.singleShot(0, guarded_report)


def _check_qgis_anchors(known_ids):
    """Phase 1b: Qt-side sweep of the long-lived anchors.

    Phase 1 only sees objects whose Python wrapper is still in
    gc.get_objects(), and phase 3 only knows records of the CURRENT session -
    an orphan from an earlier plugin generation escapes both. This sweep asks
    Qt directly, regardless of Python references or creation time:

     - findChildren() on the anchors plugin code demonstrably parents QObjects
       to (main window: docks/toolbars, map canvas: shortcuts/map tools) plus
       the cheap future-proofing anchors (project instance, layer tree view)
     - the canvas SCENE separately: markers/rubber bands are QGraphicsItems,
       not QObjects, so findChildren() cannot see them
     - the top-level widget list for parentless windows (help window, dialogs)

    Limitations: foreign-class orphans (QShortcut, ...) carry no namespace
    marker and stay invisible here (phase 3 covers them within their session);
    stale signal connections have no child relationship at all (phase 2 /
    SignalTracker territory). known_ids suppresses phase 1 duplicates.
    """
    from qgis.core import QgsProject
    from qgis.utils import iface

    candidates = []
    anchors = (
        iface.mainWindow(),
        iface.mapCanvas(),
        QgsProject.instance(),
        iface.layerTreeView(),
    )
    for anchor in anchors:
        anchor_label = _fullname(anchor)
        for child in anchor.findChildren(QObject):
            candidates.append((child, anchor_label))
    for item in iface.mapCanvas().scene().items():
        candidates.append((item, "mapCanvas().scene() (QGraphicsItem)"))
    for widget in QApplication.topLevelWidgets():
        candidates.append((widget, "top-level (kein Parent)"))

    found = False
    for obj, anchor_label in candidates:
        if id(obj) in known_ids:
            continue  # phase 1 reports this one already
        try:
            name = _fullname(obj)
        except Exception:
            continue
        if not name.startswith(_NAMESPACE_PREFIX) or sip.isdeleted(obj):
            continue
        found = True
        print(
            f"DEBUG [P1b-Anchor] !!! {name} hängt noch an {anchor_label} — "
            f"für Phase 1 unsichtbarer Waise (evtl. aus früherer Session), "
            f"deleteLater()/removeItem() beim Besitzer ergänzen."
        )
    if not found:
        print("DEBUG [P1b-Anchor] all clear — keine verwaisten Plugin-Objekte an den QGIS-Ankern.")


def check_for_leaked_objects():
    """Four phase leak detector: call on plugin unload (see module docstring).

    Phase 1 (immediate, this call): QObjects from the plugin namespace
    (_NAMESPACE_PREFIX) whose C++ object is still alive.
    Phase 1b (immediate, after the phase 1 report, see _check_qgis_anchors):
    Qt-side anchor sweep for orphans phase 1 cannot see.
    Phase 2 (deferred, see _schedule_python_leak_report): pure Python
    instances that survive the module teardown.
    Phase 3 (deferred, see _schedule_tracked_qobject_report): foreign class
    QObjects created by plugin code, reported with their creation site;
    fed by the _OriginTracker installed at plugin load.

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
                # QObjects: phase 1; classes: not instances; enum members live
                # as long as their module (see _collect_plugin_instances), noise
                continue
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
        # QObject.parent(x) instead of x.parent(): avoids the overload-shadowing
        # TypeError (e.g. QAbstractItemModel), see collapse_target in phase 3
        parent = QObject.parent(q_obj)
        while parent is not None:
            if id(parent) in leaked:
                root_id = id(parent)  # keep climbing; last hit wins
            parent = QObject.parent(parent)
        return root_id

    # process pending deleteLater() events first, so widgets just scheduled for deletion
    # (e.g. the toolbar from unload() above) are actually gone and not reported as leaks.
    # The origin tracker is still installed here ON PURPOSE: the destructor cascade
    # sends ChildRemoved for every dying child, which cleans its records and thereby
    # prevents stale addresses (freed and later reused) from becoming false positives.
    QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    gc.collect()

    # stop phase 3 recording: the filter sits on QApplication and must not
    # survive this call (see _shutdown_origin_tracker)
    origin_tracker = _shutdown_origin_tracker()

    # schedule phase 2: collect candidates as weakrefs now,
    # report only after the module teardown (next event loop iteration)
    _schedule_python_leak_report()

    # schedule phase 3: foreign classes (QShortcut, QAction, ...) that our code
    # parented to something long lived
    _schedule_tracked_qobject_report(origin_tracker)

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

        if obj is origin_tracker:
            # intentionally still alive: its destroyed() bookkeeping must survive
            # until the deferred phase 3 report, which deleteLater()s it afterwards
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
        _check_qgis_anchors(known_ids=set(leaked))
        return

    # report only the top level of registered ancestors
    for obj, count in roots_of_leaked.values():
        parent = QObject.parent(obj)
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

        _check_qgis_anchors(known_ids=set(leaked))


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
