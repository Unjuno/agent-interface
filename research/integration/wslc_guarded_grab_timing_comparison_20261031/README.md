# WSLc guarded X11 press timing with and without a short server grab

This small controlled timing pilot compares the same guarded keyboard path on a stable synthetic Xvfb target with a research-only server-grab wrapper enabled or disabled. Each fresh container records the wall-clock interval of the backend key-down call: the existing guard's observation and callback are inside that interval; in the grab arm it additionally includes grab, X synchronization and ungrab. Both arms use the same runner and fixed 100 ms key hold after the measured call. No model, game or competing X client workload is used.

| Allocation (execution order) | Mode | Key-down call (ms) |
|---|---|---:|
| u01 | baseline | 12.765 |
| u02 | grab | 12.841 |
| u03 | grab | 12.112 |
| u04 | baseline | 13.134 |
| u05 | baseline | 12.558 |
| u06 | grab | 12.987 |

The baseline median was 12.765 ms (range 12.558–13.134); the grab median was 12.841 ms (range 12.112–12.987). Their unpaired median difference is about 0.075 ms. With only three samples per arm, overlapping ranges and fixed order, this is not evidence of zero cost or a reliable overhead estimate. In particular, the server grab can stall other clients, but this pilot does not measure their delay. The 100 ms held interval, container and application startup, other workloads, and failure/recovery are not included in the key-down call timing. Baseline does not perform the additional synchronization used by the grab arm; that difference is part of the compared implementation.

All six cases were frozen together in the listed order and run once. The same runner SHA-256 is recorded in each archive. Each case completed the guarded press and release, the target saw both F events, the final owner-close release was verified and F keymap readback was up. This is a local timing observation, not a semantic safety, throughput, model-token, MAP01 or project-completion result. A controlled competing-client latency benchmark and bounded failure/custody tests are needed before considering integration.

The network-none WSLc containers used private Xvfb, one CPU and 1 GiB, a 20 s watchdog, and image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`. The read-only Python runtime subset matched the earlier fixed-patch probe; subsequent main changes were research only. The six named containers were verified exited and removed. ZIPs retain conditions, runner, observations, event records, action and release receipts and logs. `python audit.py` (normal Python mode) reconstructs the call intervals, checks the guard timing is inside each interval, compares runner hashes and verifies target events and neutral releases.
