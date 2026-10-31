# Real Xvfb idle-observation publication after expiry

This follows the [cancellation comparison](../wslc_realx_idle_publication_20261101/README.md) with a deadline comparison. A direct bridge captured a real private Xvfb target, then an instrumented `ObservationHistory.__setitem__` paused the detached insertion before publication. Both arms held the same pause until 1.2 seconds after the capture start. The first used a one-second deadline; the second used a five-second deadline. Both arms checked that the staged sequence was not visible or mintable, resumed, and then used a separate spawned owner to type `a` into an independent target.

| Observation | Expired | Within-deadline control |
| --- | --- | --- |
| Pause released relative to deadline | 200.1 ms after | 3,799.9 ms before |
| During staging | sequence 0, sequence 1 invisible, mint rejected | same |
| After resuming | capture unavailable, sequence 0, no sequence 1 | capture returned sequence 1, sequence 1 visible |
| Fresh guarded task | target recorded `a` press/release; release verified; X input neutral | same |

Separate fresh WSLc allocations were frozen before the first run and executed in the displayed order. They used draft [#10074](https://github.com/Unjuno/agent-interface/pull/10074) head `0675ab810f7ee890d0904b8a402678c81f8dbafb`, pre-run main `fdd651167b6e8646dc5ad1de2f793af3549a2a63`, pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, one CPU, 1 GiB memory limit, network disabled and no pull. WSLc reported that the memory limit did not include swap. Both launchers returned zero. [raw.zip](raw.zip) preserves conditions, source snapshot, raw outputs and target receipts, SHA-256 `56f94833c76558d3f997c5ef4ae18d7c2205f3a77b6e30aaf3a579fb7238c7ce`. The packaging audit checked frozen hashes, deadline ordering, event order, target press/release, release receipt and neutral state.

This tests a synthetic delay at one staging boundary, with deliberate concurrent direct-bridge access outside the documented serialized caller contract. It does not prove the call returns by its deadline: the fixture held execution until after expiry. The old bridge held no input, and the separate fresh task does not establish held-input recovery, natural-failure behavior, production MCP integration or MAP01 completion. Two fixed-order trials do not establish a general success rate.
