# WSLc competing X11 query during a guarded short grab

This controlled pilot follows `wslc_guarded_grab_timing_comparison_20261031`. While the same synthetic guarded key-down call runs, a second X connection on a separate thread issues one synchronous focus query. In the grab arm the thread is signaled after the guarded backend has grabbed and synchronized the private X server; the input thread waits until the probe has recorded its start immediately before calling the query. In baseline it is signaled at the corresponding point without a grab. The measured interval runs from immediately before the Python query call until its reply; it includes thread scheduling and client overhead and is not a server-only latency measurement. The separate connection shares the same process, host and X server.

| Allocation (execution order) | Mode | Other-client query interval (ms) |
|---|---|---:|
| v01 | baseline | 0.280 |
| v02 | grab | 12.063 |
| v03 | grab | 15.805 |
| v04 | baseline | 0.124 |
| v05 | baseline | 0.106 |
| v06 | grab | 13.148 |

The baseline median was 0.124 ms (range 0.106–0.280); grab median was 13.148 ms (range 12.063–15.805). In all three grab runs the probe's pre-call timestamp was inside the grab and its reply was recorded after ungrab. This shows a measurable competing-connection delay in these controlled trials, even though the preceding pilot did not resolve a key-down latency difference. It does not establish that the X request reached the server at the timestamp immediately before the Python call, isolate server delay from scheduling, or estimate latency for arbitrary applications, load or hardware. Fixed order and three samples per arm do not establish a distribution or hard bound.

All cases were frozen together, run once with the same runner, and retained. Every guarded action completed, the synthetic target saw F press and release, owner close recorded neutral release, and the F keymap was up. No model, real game, throughput workload, failure, timeout recovery, semantic correctness or MAP01 completion is tested. The global grab still permits queued changes to become visible after ungrab, and the key remains held after it. This result is evidence against describing the grab as free; it is not sufficient by itself to accept or reject the design.

The six private-Xvfb WSLc containers used network none, one CPU, 1 GiB, a 20 s watchdog and image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`. The read-only Python runtime subset matched the earlier fixed-patch probe; subsequent main changes were research only. Named containers were confirmed exited and removed. ZIPs retain runner, conditions, event and timing records, owner observations, input and release receipts and logs. `python audit.py` (normal Python mode) verifies runner identity, focus reply against the saved source binding, timing order, target key events and neutral releases.
