"""
SignalTracker: optional helper to collect signal connections and
disconnect them together, deterministically.

Background: why is this even a topic in PyQt?

Every PyQt object consists of two halves: the Python object (managed by
the Python garbage collector) and a C++ object behind it (managed by Qt,
see common/debug_checks.py). For signal connections this means:

 - Qt disconnects a connection automatically as soon as EITHER the sender
   OR the receiver (on the C++ side) is destroyed.
 - PyQt only references slots that are bound methods (self.on_xyz)
   WEAKLY: if the receiver object dies, PyQt releases the connection by
   itself. A "raw" .connect() on a method is therefore usually
   uncritical, as long as the object is allowed to die.

 - Two situations are critical:

   1. The SENDER is long lived (iface, QgsProject.instance(),
      mapCanvas()): these QGIS singletons survive every plugin and
      project reload. Cleanup then depends entirely on the receiver
      dying. If anything still holds the old instance, its slot keeps
      firing, in addition to the new instance's slot after a reload
      (double firing).

   2. The SLOT is a lambda or functools.partial: such callables are held
      STRONGLY by the signal. If the lambda captures `self`, a cycle
      forms across the C++ level that Python's GC cannot see: the signal
      holds the lambda, the lambda holds the instance, it can never die,
      the connection fires forever.

   Stale connections are not just a memory problem: if a slot fires into
   an already destroyed object, it raises an exception, and unhandled
   exceptions in slots can hard crash the whole application (PyQt then
   calls qFatal, QGIS crashes).

Whether the plugin's objects really die is monitored by the leak checks
in common/debug_checks.py. SignalTracker is the tool used to fix cases
reported there deterministically, or to avoid them in the first place.

When to use it (a recommendation, not a requirement):

 - Your own instance gets replaced at runtime (e.g. the module
   controllers on project reload in T2GArchDockWidget.reload()) AND
   connects to long lived QGIS signals.
 - lambdas / functools.partial are connected as slots.
 - Connections need to be guaranteed gone at a defined point in time.

NOT needed when sender and receiver have the same lifetime anyway, e.g.
self.btn.clicked.connect(self.on_click) in a widget: the button is a Qt
child of the widget, dies with it, and Qt disconnects the connection
itself in the process.

Usage examples:

1) QWidget/QObject as owner: fully automatic cleanup:

    class MyDockWidget(QDockWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._tracker = SignalTracker(disconnect_on_destroyed=self)
            self._tracker.track_connect(
                QgsProject.instance().readProject, self.onProjectRead
            )

    # When the widget dies (parent cascade or deleteLater()), Qt fires its
    # destroyed signal and the tracker disconnects all connections itself.

2) Plain Python class as owner: explicit call:

    class GeoEdit:
        def setup(self):
            self._tracker = SignalTracker()
            self._tracker.track_connect(iface.mapCanvas().mapToolSet, self.onToolSet)

        def disconnectSignals(self):
            self._tracker.disconnect_all()

    # Whoever replaces the instance calls disconnectSignals() beforehand
    # (see T2GArchDockWidget.reload()).

3) Defusing a lambda slot:

    self._tracker.track_connect(some_signal, lambda: self.refresh(force=True))

    # Without the tracker, the signal would hold the lambda (and thus
    # self) forever. disconnect_all() breaks the cycle.
"""

import types
import weakref
from typing import Optional

from qgis.PyQt.QtCore import QObject


class SignalTracker:
    """Collects signal connections so they can be disconnected together with disconnect_all().

    Args:
        disconnect_on_destroyed: Optional QObject owner. Its destroyed
            signal (fires when the C++ object is torn down) triggers
            disconnect_all() automatically, no manual cleanup call needed.
            Precondition: the owner actually dies (parent cascade or
            deleteLater()); whether that happens is shown by the leak
            checks in common/debug_checks.py.
    """

    def __init__(self, disconnect_on_destroyed: Optional[QObject] = None):
        self._connections = []
        if disconnect_on_destroyed is not None:
            # PyQt holds the bound method weakly: this connection keeps
            # neither the tracker nor the owner artificially alive.
            disconnect_on_destroyed.destroyed.connect(self.disconnect_all)

    def track_connect(self, signal, slot):
        """Connects signal to slot and remembers the pair for disconnect_all()."""
        signal.connect(slot)
        if isinstance(slot, types.MethodType):
            # Only remember bound methods weakly: the tracker must not
            # keep the receiver alive itself (that would be exactly the
            # leak it is meant to prevent). If the receiver dies first,
            # PyQt has already disconnected the connection anyway.
            self._connections.append((signal, weakref.WeakMethod(slot)))
        else:
            # lambdas/partials/functions: a strong reference is needed,
            # disconnect() later needs the same object.
            self._connections.append((signal, slot))

    def disconnect_all(self):
        """Disconnects all remembered connections. Idempotent, calling it more than once is fine."""
        for signal, slot_or_ref in self._connections:
            slot = slot_or_ref() if isinstance(slot_or_ref, weakref.WeakMethod) else slot_or_ref
            if slot is None:
                continue  # receiver already dead, PyQt has already disconnected
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass  # connection no longer exists (e.g. sender already destroyed)
        self._connections.clear()
