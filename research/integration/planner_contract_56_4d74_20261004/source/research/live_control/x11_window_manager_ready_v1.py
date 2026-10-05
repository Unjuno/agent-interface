"""Bounded, fixture-only Openbox readiness check; never sends user input."""
import time

from Xlib import X


def wait_window_manager(session, timeout=3.0):
    """Require an owned probe to be both viewable and managed before app launch.

    A successful X11 handshake alone does not establish window-manager readiness.
    Retry only the disposable probe's map request, never an application's input.
    This is setup time, not a runtime wait policy or a semantic completion signal.
    """
    root = session.d.screen().root
    probe = root.create_window(
        0, 0, 16, 16, 0, session.d.screen().root_depth,
        X.InputOutput, X.CopyFromParent, event_mask=X.StructureNotifyMask,
    )
    started = time.monotonic()
    deadline = started + timeout
    next_map = started
    requests = 0
    try:
        probe.set_wm_name("agent-interface-startup-readiness-probe")
        clients_atom = session.d.intern_atom("_NET_CLIENT_LIST")
        while True:
            now = time.monotonic()
            if session.openbox.poll() is not None:
                raise RuntimeError("window manager exited during readiness check")
            if now >= deadline:
                raise TimeoutError("window manager did not map/manage readiness probe")
            if now >= next_map:
                probe.map()
                session.d.flush()
                requests += 1
                next_map = now + 0.2
            clients = root.get_full_property(clients_atom, X.AnyPropertyType)
            if (probe.get_attributes().map_state == X.IsViewable
                    and clients is not None and probe.id in clients.value):
                return {"elapsed_ms": (time.monotonic() - started) * 1000,
                        "map_requests": requests, "managed_and_viewable": True}
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
    finally:
        probe.destroy()
        session.d.sync()
