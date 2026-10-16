# Xlib same-connection query/reply prefetch diagnostic A03

A03 tests whether synchronous `query_keymap()` can prefetch a focused client's key event into Python-Xlib's in-memory queue, leaving the connection socket unreadable. It addresses a possible observer limitation behind the incomplete event receipt in #7771 A03.

The predecessor A01 setup stopped on missing root privileges; A02 stopped because its root shell could not find the extracted package under the default user's home. Both are preserved, and neither candidate ran. A03 uses a fresh guest and passes `/home/taka/xlib-query-prefetch-a03` as the explicit OrbStack working directory for the root-only dependency step.

The candidate uses isolated Ubuntu 24.04 arm64 with Python-Xlib 0.33-2 and Xvfb 21.1.12-1ubuntu1.8. One XTEST connection emits one press and release; the focused event-client connection queries key state, records its internal queue, tests `select()` readiness, and then drains `pending_events()` / `next_event()`. A raw-only auditor checks exact queue, route and key-state evidence.

This can clarify a measurement limitation; it cannot establish what was in the A03 queue. It does not test DOOM, a real GUI, a model, physical input, task feedback, recovery, threat response, or MAP01. Issue #59 remains open.
