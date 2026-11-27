# V39 WSLc X11 application-effect and expiry-recovery A34

A one-shot WSLc experiment on the frozen V4 → V3 → V12 input-owner composition passed an independent raw-only audit (14/14). One admitted `a` key reached a synthetic focused X11 application, changed its counter from 0 to 1, and received the lease-expiry KeyRelease; a second X11 connection observed server key-up. The current-main strict terminal predicate accepted a known-empty owner release, and owner/thread/Xvfb cleanup passed. See [RESULT.md](RESULT.md), [PREREGISTRATION.md](PREREGISTRATION.md), `A34/output/`, and `INPUT/FREEZE.json`.

The single observed app-feedback latency was 0.479160 ms; KeyRelease arrived 0.412486 ms after the fixed 300 ms lease deadline; owner verified-empty receipt arrived 0.968183 ms after deadline. These are single-run synthetic X11 observations. They do not establish a Windows desktop, physical keyboard, game/MAP01 response, model behavior, live invalidation, task utility, or real-time guarantee.

`A30` and `A31` are pre-candidate HOLDs; `A32` stopped before dispatch on a runner-hash binding error; `A33` failed after dispatch when its test harness expected fields absent from the actual admission schema and armed the deadline too late. Their first outcomes and raw where available are preserved unpooled; no allocation was retried. A34 fixes those harness contracts and uses a new unique allocation. See `ALLOCATIONS.json`.

The exact source-main snapshot is `014bd4279a716d376f167e14fadc418f57e558f7`, before the same-day merges #8918 and #8837. WSLc used a cached immutable image with `--pull never`, `--network none`, and one CPU; the host warned that swap/cgroup enforcement is unavailable, so no hard memory-plus-swap limit is claimed.
