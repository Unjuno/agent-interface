# A01 result

**PASS: `FAIL_CLOSED_APPLICATION_CONSUMPTION_CONTRADICTION`.** The saved baseline/candidate comparison reproduces four false accepts in the current #7602 source and no false accepts in the candidate. The untouched retained pair remains `adapter_edge_brackets_paired` in the candidate. The source and raw-only auditor results are retained in `raw/A01.json` and `raw/AUDIT.json`.

The four baseline false accepts are the `application_consumption_observed=true` fields injected into either outer event or either nested `adapter_edge`. The baseline already rejected the four mutations in `physical_key_measurement` and its owner bracket. The candidate rejects all eight and returns null down/up intervals for each.

The coherent chronology sweep passes in both source versions: 15 strictly ordered DOWN/UP pairs and 85 touching, overlapping, or reversed pairs are classified as paired or incomplete respectively. Its source-bound inputs update sampling windows, request/sync boundaries, acknowledgement, and owner brackets with the chosen intervals. This both preserves the boundary result and fixes the stale sweep that initially caused 15 false test failures after the sample-window validator was added.

The saved-result auditor reports `PASS_SAVED_RESULT_AUDIT`, zero errors, baseline false-accept count 4, candidate false-accept count 0, and 15/85 on both sweeps. During development, the 18 focused AST-extracted projection tests passed on the same candidate source; `py_compile` and `git diff --check` passed. The full test-module import was unavailable because Pillow and an imported source module are absent from this checkout. The experiment ran on host Python 3.14.5 after the pinned OrbStack image preflight stopped with `STOP_CONTAINER_IMAGE_UNAVAILABLE`; no image was pulled.

This is deterministic projector evidence. It does not establish that the X-server keymap sample represents an OS-level physical dwell, application input consumption, useful game feedback, safety, recovery efficacy, or MAP01 progress. Issue #59's live gates remain open.

**Supplemental audit repair:** the original auditor trusted each row's saved `expected_ordered` bit. It now derives strict order from the recorded bounds (`down[1] < up[0]`) and rejects invalid interval shapes. Two regression tests pass: the untouched saved bundle remains valid, and swapping one paired and one incomplete classification while preserving the 15/85 aggregate is rejected. This strengthens only the saved-result consistency check; it does not rerun or expand the frozen source comparison.
