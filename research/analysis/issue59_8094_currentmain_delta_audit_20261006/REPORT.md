# #59 / #8094 current-main production-delta audit

Decision: **PASS_CURRENT_MAIN_DELTA_NONCONFLICT_SCOPED**

At intake, GitHub compare reported #8094 as 66 commits ahead / 92 behind current main, which by itself makes the whole PR unsuitable for direct merge. This audit isolates the execution-facing delta instead of treating branch age as a code conflict.

| path | base | intake main | #8094 | classification |
|---|---|---|---|---|
| `research/doom/doom_batch_key_measurement_backend_v1.py` | — | — | `5b07504d` | CANDIDATE_ADD_CLEAN |
| `research/doom/doom_owner_thread_release_batch_backend_v1.py` | `193c2bd2` | `193c2bd2` | `0d079174` | MAIN_UNCHANGED_CANDIDATE_ONLY |
| `research/doom/map01_overlap_controller_v39.py` | `e9b43797` | `e9b43797` | `e2de3df2` | MAIN_UNCHANGED_CANDIDATE_ONLY |
| `research/doom/session_map01_v12.py` | `e7010353` | `e7010353` | `7ccd4896` | MAIN_UNCHANGED_CANDIDATE_ONLY |
| `research/doom/session_map01_v15.py` | `f71ca014` | `f71ca014` | `2d6974c2` | MAIN_UNCHANGED_CANDIDATE_ONLY |
| `research/doom/v39_measurement_backend_selection_v1.py` | — | — | `c7d84b1b` | CANDIDATE_ADD_CLEAN |
| `research/live_control/input_owner_v12.py` | `d11a9b13` | `d11a9b13` | `5622e684` | MAIN_UNCHANGED_CANDIDATE_ONLY |
| `research/live_control/input_transition_owner_v4.py` | `ac1cc0e6` | `ac1cc0e6` | `159c5d31` | MAIN_UNCHANGED_CANDIDATE_ONLY |
| `research/live_control/key_edge_measurement_v1.py` | — | — | `775c5896` | CANDIDATE_ADD_CLEAN |
| `research/live_control/observable_signal_guard_v2.py` | `c0955f97` | `c0955f97` | `1e7ad4f9` | MAIN_UNCHANGED_CANDIDATE_ONLY |
| `research/doom/map01_motor_responder_v10.txt` | `9ee9fe93` | `9ee9fe93` | `ef32ef84` | MAIN_UNCHANGED_CANDIDATE_ONLY |


Summary: **11/11 nonconflicting at the frozen source boundary** — 3 clean additions and 8 candidate-only edits whose intake-main blobs are exactly the merge-base blobs. No selected path has a current-main edit that must be reconciled.

This materially narrows the integration problem: #8094 does not need a semantic rebase merely because main advanced elsewhere. It still needs a small, current-main-based candidate containing the relevant source changes and tests, followed by exact-current-tree execution/review. Do not merge the 1467-file historical/evidence branch on the strength of this audit.

The model-prompt line is included because #8094 changes it: it tells the model that prior health/ammo comparisons are state observations and that viewport change alone is not task effect. Its main blob is also unchanged from merge base.

## Limits
This is Git object/source compatibility only. It does not validate imports, runtime behavior, the native evidence package, live input, game behavior, useful feedback, recovery, or #59 completion.
