# Split-step terminal-cleanup receipt fix 02

Date: 2026-10-04
Result: `PASS_CONSTRUCTION` for the tested release-batch behavior; `HOLD_NATIVE_VALIDATION`.

## H/T/D/C/U

- **H — Hypothesis:** after a successful executor step buffers an explicit per-key release while another key remains held, terminal `release_all()` bypasses adapter `raw()` and drops the held set. Without an adapter override, the earlier valid per-key receipt is never sampled or published.
- **T — Target:** candidate head `fbed929f629dabaa9ae752019d0ee7151d4d2298`, specifically `research/doom/doom_typed_release_backend_v3.py` and inherited `research/live_control/session_v5.py::Backend.release_all`.
- **D — Design:** deterministic two-key case (`a`, `space`): step 0 explicitly releases `a`; terminal cleanup releases the remaining owner state. The regression test extracts and executes the actual `session_v5.Backend.release_all` method AST in isolation, avoiding import of its unrelated GUI/Pillow dependency. RED on the unmodified candidate; add an adapter cleanup override that delegates to the production method, samples owner state once, publishes only already-recorded explicit-up receipts, and marks cleanup provenance. Cleanup verification false must keep the batch's `owner_transition_verified` false.
- **C — Criteria:** emit exactly the recorded `a` receipt (never synthesize a `space` per-key receipt); sample owner state once after cleanup; preserve the step identity; verify the batch only when the explicit-up and terminal-cleanup evidence pass. A cleanup-negative control must retain the row but fail closed.
- **U — Unknowns:** this is a deterministic test double for `InputOwner`, not an X server, OS keyboard, ViZDoom, live threat exposure, user-visible effect, useful-feedback, recovery, or task-completion test. Physical release timing and #59's matched-condition threat-control exit gate remain unverified.

## Outcomes

The original candidate suite was 18/18 green but its test parent implemented `release_all()` by looping through `raw()`, unlike the inherited production method. Applying the exact inherited method to the case produced a counterexample: owner calls `[('up', 'a'), ('release', None)]`, emitted receipts `[]`, pending receipt `['a']`, held set empty, and no post-cleanup `input_state` sample.

An initial independent test invocation used the PR's base branch (`a35406ff`) instead of PR #7378's head (`fbed929f`) and an incomplete sparse checkout; it produced import/file-not-found errors and is not treated as a candidate result. After switching to the exact PR head and materializing the test's declared source dependencies, the parent suite passed 18/18 and the counterexample above reproduced.

The new regression first failed as intended: expected `['a']`, got `[]`. After the fix:

- `python3 -B -m unittest -v test_doom_typed_release_backend_v3` — **19/19 PASS**.
- `python3 -B -m unittest -v test_input_transition_owner_v3` — **8/8 PASS**.
- `python3 -B -m unittest -v test_overlap_controller_v39_wait` — **7/7 PASS**.
- Source compilation via Python `compile()` — **PASS**.
- `git diff --check` — **PASS**.
- Cleanup-negative control — receipt retained, `terminal_cleanup_verified=false`, `owner_transition_verified=false`.

Related broader test attempts were incomplete, not passes: `test_doom_typed_release_backend_v2` and `test_map01_overlap_controller_v39` could not import because Pillow (`PIL`) is absent from this host. The wait-only controller module did run and passed as recorded above.

## Container STOP and reproducibility

Host: macOS / Python 3.14.5. The intended OrbStack container path was not started. `docker info` returned server `29.4.0 OrbStack`, but read-only `docker ps` failed with containerd `open ...content/blobs/sha256/...: operation not supported`. No image operation, daemon repair/restart, VM change, or live allocation was attempted. Local construction tests are not container validation.

Re-run the focused checks from `research/doom/` and `research/live_control/` as listed above. The test loads the inherited cleanup method from the checked-out `session_v5.py`; do not replace it with a test parent that calls `raw()`.

## Frozen inputs

- Parent PR head: `fbed929f629dabaa9ae752019d0ee7151d4d2298`.
- Parent cleanup source SHA-256: `041da34620bfb425e14aa1cafc09ee5481fc378389fe0e716f3d8710b1b0cd12`.
- Candidate backend SHA-256 after fix: `61d59197bd9d20bfaac4c12a6ad7ac582fdd9bbb207d88a2b5a427b7fa8706fe`.
- Candidate test SHA-256 after fix: `8e5d282ed165ff724f095c5de02c4ac957cf592259e65d682c1fd941633d9d09`.

This result fixes only the construction-path loss of buffered per-key receipts. It does not authorize or satisfy a new live allocation and does not close Issue #59.
