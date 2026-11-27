# Current-main composed suite rerun — bounded cancellation response fix

## Baseline

On exact main `1db2df19bbc311bfd77df97e7223274480aaf6ac`, the same ten-module suite ran 219 tests. Optimized mode passed 219/219; normal mode had one `KeyError` in `test_prearmed_cleanup_can_precede_retired_owners_queued_down` when it indexed `owner_process_retired` on the immediate cancellation response. Both raw baseline logs remain in `normal.log` and `optimized.log`; baseline exit was 1.

## Diagnosis and correction

The public cancellation endpoint has a 300 ms caller response budget while cleanup retains custody and can continue after that response. Under load it may legitimately return `pending`. The test had assumed the cleanup receipt would always be terminal in the first response. It now polls the same call ID within a bounded 3 s window and then requires the terminal owner-retired receipt, `release_confirmed=false`, `cleanup_status=UNKNOWN`, null task success, and replay denied.

A deterministic test seam adds 350 ms to the fake post-retirement cleanup, verifies that the initial public response is `pending`, then retrieves the same operation to its terminal state. The original safety assertions remain. No runtime implementation code changed.

## Verification

- Exact pending branch: `test_prearmed_cleanup_can_precede_retired_owners_queued_down` passed normal and optimized, Docker exit 0, with the 350 ms delay forcing the pending response.
- Same ten-module composed suite on current main plus the test-only patch: 219/219 normal (95.081 s), 219/219 optimized (96.735 s), Docker exit 0. Raw outputs are in `rerun-after-deterministic-pending-02/`.
- After Docker Desktop restart and removal of WSL `vmIdleTimeout`, the same candidate suite passed 219/219 normal (98.331 s) and 219/219 optimized; Docker exit 0. Raw outputs and runtime conditions are in `post-docker-restart-20261104-01/`.
- An earlier full rerun after the initial poll change also passed both modes; it is retained separately.
- The preceding five-module prefix passed 169/169 and captured the terminal `cancel_requested` receipt. Focused diagnostic logs are retained.
- `candidate-test-fix.patch` and the candidate file SHA identify the exact test-only change from main.

## Conditions and scope

Pinned image `agent-interface-xvfb-mcp:late-input-r19` (`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`), Docker Engine 29.8.1, active host `.wslconfig` 32 GB / 8 CPU / 16 GB swap / gradual reclaim, with WSL idle timeout unset for the post-restart rerun. Each full-suite container had no network, 2 CPUs, 4 GiB memory and total memory+swap, 256 PIDs, read-only source, writable evidence mount. The full suite is synthetic Fake X/provider composition only; no provider generation or GUI action occurred.

This resolves the flaky test assumption about a bounded public response, not a live cancellation/release defect. It proves no live provider behavior, end-to-end efficiency, WSLc, MAP01, or long-term Docker stability.
