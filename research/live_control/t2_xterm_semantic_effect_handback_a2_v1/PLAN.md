# T2 XTerm semantic-effect handback A2

Issue #1543. Parent science #1537; repaired delivery precondition #1539; absolute-deadline mechanism #1518.

Only repaired construction precondition: helper READY is published after raw PTY mode is active; controller waits READY, focuses XTerm top-level, verifies focus readback, then admits XTEST x.

Formal science remains: frontier+40ms, offsets34/36/38/39, hold8ms, semantic delays10/13ms, timeout8ms after actuation receipt, p95<6/max<8, 16 matched pairs/32 positives, 4 NO_EFFECT controls, formal1/reruns0.
