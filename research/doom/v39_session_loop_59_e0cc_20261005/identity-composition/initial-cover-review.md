# Initial-cover identity barrier and retained full-run review

## Executable extracted-branch regression

`tests/test_initial_cover_identity_barrier.py` extracts the initial `policy_invalidation` branch from the selected V39 controller AST and executes the branch with its production resolver, cancellation/release validator, and `wait_for_invalidation_frame` helper. A scripted queue supplies an accepted initial cover, cancellation acknowledgement, verified empty release, then a same-sequence wrong-focus frame, a stale-capture frame, and the exact identity-matching frame. The positive case verifies the branch records the original `source_image` separately from `invalidation_frame_image`, and that planner/action admission remains `not_started`. Negative cases verify a missing acceptable frame raises `TimeoutError`, and an unverified/nonempty release raises before accepting a frame.

Selected controller SHA-256: `69c691d8c4413839d0673605215064efa3091174c390c8ef8494c19bdf0523a9`.
Test SHA-256: `9909d10c0ed3bad0e755aacb01ef0e2aee550380b04394407ec16490b108bc8e`.

Using the bundled Python runtime, composed source passed 3/3 tests (`receipts/initial-cover-composed-v7.*`). Baseline source failed the two barrier-specific cases and passed the release guard case (`receipts/initial-cover-baseline-v7.*`), as expected: it proceeds without consuming the matching frame and does not time out when the frame is absent. This is a pure extracted-branch unit; it does not execute V39's full loop or a child process.

Earlier construction attempts are retained in `receipts/` with their stderr/exit files and source snapshots `test_initial_cover_identity_barrier-v1.py.txt` through `-v4.py.txt`. Initial system-Python/Pillow and missing-import failures, followed by AST harness construction errors, were repaired before the v7 run; v7 is the first passing executable regression. No prior failed output was overwritten.

## Raw review of full-04 through full-07

I spot-checked the raw controller reports, child receipts, fake-external state, and harness timelines alongside the retained `raw-audit-v1.json` (219 checks, all passing; SHA-256 `cefba2d59644a5be05c3bcbe9594119d7e94fd7a4148c6be2c0036e04c510792`).

- **full-04 normal control:** child exit 0; two primary plans each release the three keys in one shared batch and retain matched per-key measurement records. No policy invalidation occurs. Final fake key state is empty and all five X connections close.
- **full-05 hard health invalidation:** turn 2 is interrupted before its later `active/eligible` answer returns. The answer is discarded with `REJECTED_POLICY_INVALIDATED`, and no `plan-1` submit occurs. The next model turn uses health source sequence 10, whose identity matches the seq10 invalidation (capture timestamp, binding, and frame RGB hash). The sequence is interrupt → late eligible return → verified cover cancellation/release → next prompt. The frame was naturally available in this run; this is not a delayed-frame race demonstration.
- **full-06 unknown health then recovery:** the same ordering holds; invalidation seq10 is `UNKNOWN/signal_unavailable`, the late eligible answer is discarded, and no `plan-1` submit occurs. A source-refresh observe yields seq11 before the next model prompt, whose source signal is seq11. Child exits 0 and final fake key state is empty.
- **full-07 failed release:** turn 2 is interrupted, then its late eligible answer returns. Cancellation cannot verify an empty release, so the controller raises `RuntimeError("invalidated cover did not verify empty release")`; no `plan-1` submit or third model turn occurs. The report correctly records `cleanup_complete=false`, fake key 24 still down, and all five X connections closed. The remaining down key is an intentional synthetic failure result, not evidence of successful cleanup.

All four full runs use actual V39 and child Session code with fake external X/game/capture/HUD/model seams. They provide no live X11, game, model, task-effect, or performance evidence. The successful invalidation traces do not exercise a frame delayed until after release; the new extracted-branch unit adds identity rejection and absent-frame checks but still does not establish full-loop scheduling under that race.
