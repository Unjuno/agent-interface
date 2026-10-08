# Xlib same-connection query/reply prefetch diagnostic A02

A01 stopped before the candidate because dependency setup lacked root privileges; that log and disposition are preserved. A02 changes only the setup execution identity to explicit root, verifies UID 0, and uses a fresh guest.

This bounded test checks whether a synchronous `query_keymap()` can prefetch a focused client's key event into Python-Xlib's in-memory queue, leaving the connection socket unreadable. It was prompted by A03's event-list-empty timeout; A03's raw and disposition remain unchanged.

The candidate uses one isolated Ubuntu 24.04 arm64 OrbStack guest with Python-Xlib 0.33-2 and Xvfb 21.1.12-1ubuntu1.8. One XTEST connection emits one press and release; a separate focused client connection queries key state and then tests `select()` readiness before draining `pending_events()` / `next_event()`. A raw-only auditor checks exact route, queue and key-state evidence. No DOOM process, model, real GUI, physical input, or network-facing X server is used.

The result can explain an observer limitation, but cannot establish what was in A03's unrecorded Xlib queue. It says nothing about real OS delivery, physical release, task feedback, recovery, threat response, or MAP01. The Issue #59 live gate remains open.
