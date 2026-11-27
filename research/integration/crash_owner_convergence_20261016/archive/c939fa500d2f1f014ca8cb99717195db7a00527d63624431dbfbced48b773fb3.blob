# Local verification and audit

- Candidate run: one invocation, exit 1, formal experiment status STOP. See RUNNER/candidate.log.txt and results/A01/RAW.json.
- Raw-only auditor: python3 -B audit_raw.py under WSL Ubuntu; exit 0, PASS_RAW_CONSISTENCY. It verifies SHA-256 identity and the recorded two-arm X key/owner lifecycle facts. It retains formal_decision: STOP.
- Raw SHA-256: 3fbd2c2588b13d3ca22543db7a70cb433bcd6faf415188077f3e6ac4e96cae0f.
- Audit SHA-256: 909e93bc07fa9521ec71e8a69203edb85ba40887d83c8ccdb2ed6a060a2b425e.
- Focused software regressions on frozen current-main source: python -m unittest -v research.doom.test_map01_overlap_controller_v39 research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency research.doom.test_map01_overlap_controller_v39_dual_signal research.live_control.test_persistent_planner_adapter_v2 research.live_control.test_input_transition_owner_v4 research.live_control.test_input_owner_v12_explicit_up_cancel research.live_control.test_input_owner_v12_cleanup_after_explicit_up — 61 tests, all passed.

One earlier test command used research.doom.test_persistent_planner_adapter_v2, which does not exist; that invocation had one import error. The corrected module is under research.live_control, and the complete corrected command passed. This is separate from the one-shot candidate run.

git diff --check is run before commit. No live game, physical keyboard, or model was used.
