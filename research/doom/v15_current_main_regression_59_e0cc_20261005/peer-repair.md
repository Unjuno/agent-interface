# Focused AST-fixture repair result

This repair changes only two test modules; production source is unchanged.

`test_v39_measurement_session_comp.py` now supplies `HERE` and `RESEARCH` as the production V15 entrypoint expects. In `session_map01_v15.py:130-131`, the selected bridge is `HERE / 'doom_batch_key_measurement_backend_v1.py'` and the owner is `RESEARCH / 'live_control/input_owner_v12.py'`. The extracted-main test verifies those exact resolved paths as well as option propagation, rather than merely preventing the missing-global error.

`test_overlap_controller_v39_wait.py` now compiles and exercises the actual `wait_for_invalidation_frame` helper used by the controller. The regression feeds a wrong binding, stale capture, wrong frame hash, and finally the matching fresh frame; only the last is accepted. The initial-cover tests carry the same identity fields and verify the returned decision includes the matching `invalidation_frame_image`. This covers the production helper at `map01_overlap_controller_v39.py:423-440` and its initial-cover use at lines 1459 onward; it is still an extracted-unit test, not a full controller/session execution.

Validation used `python3 -B` and `python3 -O -B` on each module. Normal and optimized runs both passed: session module 3/3, wait module 16/16. Exit receipts are all zero; `git diff --check` passed.

SHA-256:

- `test_v39_measurement_session_comp.py`: `9350421ff834dfd9f697468b7437b8fed0248fdfd637c1fc5dfc9ecdd81fac26`
- `test_overlap_controller_v39_wait.py`: `f169b3ca815d06fbeb89e0d79c1e80b8cc61ff8b7cc68ff4cfd558ff1f685b8f`

Captured stdout/stderr/exit files and `tests.patch` are retained alongside this report. This is focused test-fixture maintenance and technical verification, not a merge or quorum vote.
