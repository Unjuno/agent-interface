# Detached idle-history insertion cost on WSLc

Two WSLc containers measured the local metadata cost of the detached `ObservationHistory.fork()` prototype in draft [#10074](https://github.com/Unjuno/agent-interface/pull/10074), source snapshot `0675ab810f7ee890d0904b8a402678c81f8dbafb`. The in-place insertion baseline does not provide the prototype's isolation guarantee; this is a cost comparison, not an end-to-end computer-control comparison. The conditions were prepared before either run, against then-current main `df30c4bddb24e1f46fbfba78c742348d9318b3cc`.

WSLc had returned `WslC/E_FAIL` following a Docker Desktop restart, but subsequently responded to `wslc list` and `wslc images`; the cause of the transient failure was not established. The two new allocations ran with network disabled, one CPU, a 1 GiB memory limit, and the existing pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, without pulling. The source snapshot, conditions, all samples and launcher outputs are preserved in [raw.zip](raw.zip), SHA-256 `643db2c4abed51c239b1a6052345d51136c0bb300c157736b612eaf41fb8bc82`.

Each arm constructed synthetic history metadata at four sizes with a shared 16×16 image, and measured 41 paired insertions per size, alternating baseline and fork order. One arm used ascending sizes and the other descending. Deletion and disposal after insertion are outside the timed region. A separate `tracemalloc` measurement covers new fork and insertion allocations, not the history's preexisting memory.

| Retained entries | In-place median, ms (ascending / descending) | Fork + insertion median, ms (ascending / descending) | Fork peak newly traced bytes |
| ---: | ---: | ---: | ---: |
| 0 | 0.00039 / 0.00039 | 0.00064 / 0.00064 | 640 |
| 1,000 | 0.00046 / 0.00044 | 0.00256 / 0.00250 | 37,496 |
| 10,000 | 0.00052 / 0.00057 | 0.02112 / 0.02093 | 295,536 |
| 100,000 | 0.00229 / 0.00169 | 0.55643 / 0.56330 | 5,243,504 |

Both runs returned zero. The packaging audit checked frozen file hashes, trial counts, order, positive timings, recomputed medians, stdout against the saved result, and archive hashes. The local cost increases with retained metadata in this synthetic workload, consistent with the earlier [Docker measurement](../docker_idle_history_fork_cost_20261101/README.md); the environments and images differ and are not a controlled platform comparison. This does not establish a latency budget, end-to-end speed, input release, bounded recovery, or task effects. Capture, disk reload, IPC, models, concurrent observations and real GUI behavior were not measured; the two arms share one machine. A bounded or structurally shared history merits investigation without weakening the staging and cancellation guarantees.
