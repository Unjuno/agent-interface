# Read-only review: PR #8094 source-delta attribution

Reviewed the locally retained Git objects at own head `59e307adde701dc3e061ee3ff124c5982c20fcc9`, prior current-main pin `21fecd58b9de30073c97234124e73b78c67d4b0c`, newer current-main pin `95316efef54b092fc2f0264539223830cdb9ba21`, and frozen source head `2b0cb591c3ebcb84d1db983612613850c08fffea`. No files or branches were changed and no tests/runtime were executed.

## Attribution

The four paths differ between current main and own head, but that alone does not show that intervening main changes invalidated the earlier source export. The merge base of own head and current main is `21fecd58b9de30073c97234124e73b78c67d4b0c`; comparing that main pin with `95316efef54b092fc2f0264539223830cdb9ba21` produces no semantic diff in these four files when line-ending changes are ignored. In contrast, the intended PR implementation changes them relative to main:

- `doom_owner_thread_release_batch_backend_v1.py` makes the owner class injectable so the measured backend can preserve the ordered release-batch wrapper.
- `session_map01_v12.py` adds the opt-in per-key source closure and rejects startup if the actually imported raw owner does not match the declared owner path.
- `session_map01_v15.py` selects the measured bridge only for the explicit option and retains that backend through the V15 startup wrapper.
- `map01_overlap_controller_v39.py` carries the branch’s typed identity, key-edge measurement, source feedback, and invalidation/frame-barrier integration. This is a substantial intentional source delta, not a new change introduced by the newer main pin.

The four source blobs at own head `59e307adde701dc3e061ee3ff124c5982c20fcc9` are byte-identical to frozen head `2b0cb591c3ebcb84d1db983612613850c08fffea` and to the corresponding files in the retained 81-file source export. Their SHA256 values, in the order above, are `89269de6f79d1dea2929f4b4f12e4b7baa0d041f3e389e173f257a4bbc95e73e`, `3352d1dee893d23e2cc34dfb644464963d7110963595dbdd540949cca3ddff35`, `4098ce2131608cc509d1ba7d3978e6b1c76a81293c8eb3d575805a0dd296f1de`, and `2cfe90b68cad848377818ca121d8c147f8be9179a5514d269159e76442d9ac2e`. This supports applicability of that frozen export to the PR’s own source at both pins; it does not replace exact-current-main focused integration tests.

## Existing focused entrypoints

For the backend/owner and opt-in startup boundary, the directly relevant existing files are `research/live_control/test_batch_key_measurement_composition.py`, `research/live_control/test_input_owner_v12_key_measurement.py`, `research/live_control/test_input_owner_v12_cleanup_measurement.py`, `research/doom/test_map01_v15_perkey_backend_selection.py`, and `research/doom/test_perkey_owner_source_guard.py`. For the V39 consumer and session handoff, the focused entrypoints are `research/doom/test_map01_overlap_controller_v39.py`, `research/doom/test_map01_overlap_controller_v39_initial_frame.py`, `research/doom/test_v39_measurement_session_comp.py`, and `research/doom/test_map01_v39_typed_state_feedback.py`. These are suggested existing tests only; I did not run them.

## Conclusion and scope

The cited four-file difference is real as a PR-versus-main source delta. The available objects do not support attributing it to changes between the prior and newer main pins: those main versions are semantically identical on these paths. The old 81-file export still matches the PR source blobs for these four files, while its broader applicability still needs whatever exact-current-main merge and focused regression evidence root is separately collecting. This review does not make a merge, current-main integration, or gameplay qualification claim.
