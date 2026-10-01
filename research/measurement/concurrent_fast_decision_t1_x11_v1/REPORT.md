# #1384 preformal construction stop

Decision: `PREFORMAL_CONSTRUCTION_STOP_XIO_XSERVER_TEARDOWN`. Scientific disposition: **NONE**.

The frozen one-pair construction allocation did not produce a complete result artifact. The supervisor exited nonzero with `XIO: fatal IO error 22 (Invalid argument) on X server ":0"` after 233 requests, with17 events remaining. Both fresh case directories had been created, so the allocation is consumed and is not rerun. `CONSTRUCTION_RESULT.json` and construction audit were never written; complete/poolable rows=0; formal0/reruns0.

A residual Xvfb/display `:0` remained after the failed supervisor and was manually terminated. Post-cleanup residual Xvfb/display sockets=0. Frozen source hashes remained unchanged.

Posthoc harness hypothesis only (not scientific evidence): the current supervisor runs successive Tk/Xlib sessions in one long-lived Python process while each case tears down/recreates Xvfb. A fresh successor should change exactly one orchestration factor: one Python child process per session, preserving the same per-session fixture, `perf_counter_ns` clock, selector, 0/40ms frontier schedule, 5ms cadence, XTEST action semantics, scorer, thresholds, and formal budget.
