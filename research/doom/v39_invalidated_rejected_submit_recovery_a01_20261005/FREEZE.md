# V39 invalidated-submit rejection boundary — A01

H — If a hard typed observation invalidates a V39 initial cover while its submit is still pending, the executor may reject that submit because its expected sequence is stale. The admission gate must distinguish this from an accepted cover before sending cancellation or waiting for release/terminal events.

T — On PR #7904's exact current-main composition, use source-extracted production `wait`, `submit_cover`, and initial admission gate with a deterministic FIFO: hard observation (health below floor), id-less stale-sequence `rejected`, then a hypothetical unmatched cancel acknowledgement. The accepted control uses observation, accepted, matched cancel, verified input release, and cancelled terminal. No game, GUI, runtime, model, or input backend is started.

D — Rejected case passes only if the gate drains the submit response, records `status=rejected`, sends no cancel, starts no planner, creates no cover ID/terminal receipt, and returns within the bounded event wait. Accepted control passes only with matched cancellation, verified empty release, and cancelled terminal.

C — Deterministic synthetic FIFO, stub process/monitor, and the source-extracted Python test harness. This does not exercise executor scheduling or validate the real session's event timing.

U — This isolates a recovery bug in PR #7904's initial-admission integration. It does not establish fresh visual-threat perception, live V39 response, physical key state, application effect, useful feedback, survival, MAP01 progress, or exit. The private live-game allocation remains unassigned.

Frozen base: current main `2373e2c80f9385041c18b2df64405a6ffb7693ce`; active repair PR #7904 at `9aca6fec307a0995a0112767271bbaca9798425a`.

The baseline controller snapshot is the exact PR #7904 head file before this repair, SHA-256 `091eebed4bee6d4f385fd6d0431bfbecae7f8778f1949e841df2edacdda8dfa1`.

Exact A01 candidate files (PR #7904 plus this repair), recovered from commit `bf35fe0f2` before the active PR branch advanced:

- `candidate_controller.py` SHA-256 `ee966869d45f4b3f261c5f675e100edd9ed2f20fa9fc42b9523e2aeb7b065c14`
- `candidate_test.py` SHA-256 `da4628b61d255c4d53426e41c85b01665c26e3289bb3c4a587b75b5c3cdca827`

The open PR branch advanced to `bd455dd9df392ce2c792d501053cd427b1af0ccd` with a separate cover-renewal fix while this test was underway. The repaired A01 regression was rerun against its frozen candidate snapshot; the combined PR branch was also tested after rebasing this fix.

Candidate command: `python -m unittest research.doom.test_overlap_controller_v39_wait -v`.
Baseline reproduction command: `python research/doom/v39_invalidated_rejected_submit_recovery_a01_20261005/baseline_replay.py`.
