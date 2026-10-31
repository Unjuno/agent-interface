# Detached idle-history insertion cost on Docker Desktop

On 2026-11-01, two independently created Docker Desktop containers measured the local metadata cost of the `ObservationHistory.fork()` prototype from draft [#10074](https://github.com/Unjuno/agent-interface/pull/10074), source snapshot `0675ab810f7ee890d0904b8a402678c81f8dbafb`, against the in-place insertion used as a performance baseline. The baseline does not provide the prototype's isolation guarantee. This is not an end-to-end computer-control comparison.

The previously prepared WSLc experiment was not run: `wslc list` returned `WslC/E_FAIL` after Docker Desktop was restarted. The present experiment instead used locally available Docker image `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`, with networking disabled, one CPU, a 1 GiB memory limit and no image pull. This is Docker evidence, not evidence of a successful WSLc run. The image was verified to include Python 3.11.2 and Pillow 10.2.0. The source snapshot, both conditions, implementation, all samples, and launcher outputs are in [raw.zip](raw.zip), SHA-256 `472e5525b9d72c3d6727d926cf1cbb06be49bb83768cfbbe672ddb8b0e4703c4`.

Before either run, the two arms and file hashes were frozen. Each arm constructed synthetic history metadata at four sizes, with a shared 16×16 image, and measured 41 paired insertions per size, alternating the order of baseline and fork operations. The first arm used ascending sizes; the second used descending sizes. Each measurement excludes deletion/disposal following the timed insertion. A separate `tracemalloc` measurement covers allocations made by the fork and insertion, not the memory already held by the history.

| Retained entries | In-place median, ms (ascending / descending) | Fork + insertion median, ms (ascending / descending) | Fork peak newly traced bytes |
| ---: | ---: | ---: | ---: |
| 0 | 0.00042 / 0.00042 | 0.00066 / 0.00064 | 640 |
| 1,000 | 0.00048 / 0.00043 | 0.00260 / 0.00253 | 37,496 |
| 10,000 | 0.00057 / 0.00058 | 0.02296 / 0.02114 | 295,536 |
| 100,000 | 0.00263 / 0.00221 | 0.74340 / 0.57111 | 5,243,504 |

Both runs returned zero. The packaging audit checked frozen hashes, sample counts, order, positive timings, recomputed medians, stdout against the saved result, and archived file hashes. The data show increasing local fork cost for this synthetic workload; they do not establish a latency budget, a production speedup, safe input recovery, or successful task effects. Capture, image decoding, IPC, model calls, concurrent observations, cleanup, real GUI operation, and long-running memory retention were not measured. The two arms share a machine and cannot characterize broader machine-to-machine variability. The baseline deliberately lacks detached staging, so the table compares cost rather than equivalent correctness. A bounded or structurally shared history is a candidate for further investigation, subject to preserving the staging and cancellation invariants.
