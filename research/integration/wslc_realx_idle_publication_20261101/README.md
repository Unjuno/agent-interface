# Real Xvfb idle-observation staging and cancellation

On a private WSLc Xvfb server, an instrumented direct bridge paused after inserting an observation into its detached staging history, before publication. While paused, the test attempted to read and mint the not-yet-published sequence. It then either cancelled or resumed publication. After the bridge closed, a fresh spawned owner sent `a` through guarded input to a separate X client which recorded its own received events and value.

The two corrected arms, `publication-d01` (cancel) and `publication-d02` (publish control), used separate new allocations with fixed order and pre-frozen source/conditions. Both used draft [#10074](https://github.com/Unjuno/agent-interface/pull/10074) head `0675ab810f7ee890d0904b8a402678c81f8dbafb`, main `016c9bf9776b5f6c2d3033acdd0311770dd63d24`, pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, one CPU, 1 GiB memory limit, no network and no pull. WSLc reported that its memory limit did not include swap.

| Observation | Cancel | Publish control |
| --- | --- | --- |
| While paused | sequence 0; sequence 1 invisible; mint rejected | sequence 0; sequence 1 invisible; mint rejected |
| After release of pause | cancel requested; capture unavailable; sequence 0 and no sequence 1 | capture returned sequence 1 and sequence 1 visible |
| Fresh owner | target value `a`, recorded press and release, guarded release verified, X key and button state neutral | same |

The direct-bridge staging race deliberately injects a pause and a concurrent mint/cancel, outside the prototype's documented requirement that callers serialize bridge operations. It probes a boundary, not general concurrent safety. The separately spawned owner exercises an actual subsequent guarded task, but the old bridge held no input. It does not establish held-input recovery, hard deadlines, a production MCP integration, MAP01 completion, or reliability under natural failures.

Two failed precursor attempts are retained. `publication-b01` accidentally used an older source snapshot while its frozen conditions named the draft head. That inconsistency was discovered by comparing the bridge file hash with the draft after the run: the result showed sequence 1 visible and mint succeeding before cancellation, but **is not evidence about the named draft head**. `publication-c01` used the correct draft and showed the expected staging/cancel observations, but the runner lacked a multiprocessing main guard; a spawned child re-executed the runner, leading to `EOFError` and UNKNOWN cleanup for the fresh owner. Thus it failed the whole task and cannot count as a successful recovery. The corrected pair used new allocations rather than overwriting either failure.

[raw.zip](raw.zip) retains source snapshots, frozen conditions, logs, output, target receipts and both failures. SHA-256: `02f0eb1caedbd34451df61aa8fd280cdfb01e3127b2436ceae9fa5a237b47ee4`. The packaging audit checks all frozen source hashes, relevant state and event order, target press/release, release receipts, neutral state, and every archived file hash. The experiment does not quantify general success rate from two fixed-order trials.
