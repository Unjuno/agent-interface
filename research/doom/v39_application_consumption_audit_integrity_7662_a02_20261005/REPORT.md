# A02 — saved interval auditor label-swap check

## Question and frozen scope

The draft #7662 result auditor checks each sweep row's reported `status` and exposed intervals against the row's raw `expected_ordered` label and checks an aggregate 15/85 split. This A02 tests whether the auditor independently derives that label from `down` and `up` chronology.

The freeze pins the then-current main SHA, the exact audited draft source commit `719ef679c977a925db3a6d1fe15f9cd93cf2b42c`, all 19 files in its A01 evidence package, and the one mutation. In both baseline and candidate sweeps, row 4 is changed from ordered to incomplete and row 15 from incomplete to ordered; statuses and exposed interval fields follow those swapped labels. The total remains 15 paired / 85 incomplete. The candidate run itself is not rerun.

## Result

The original saved-result auditor passed the untouched raw and the mutated raw (both exit 0, same stdout SHA-256, `PASS_SAVED_RESULT_AUDIT`). Independent recomputation from `down[1] < up[0]` finds four `expected_ordered` disagreements: rows 4 and 15 in each of the two implementation sweeps. It also finds the expected downstream status/output inconsistencies for those same rows. This reproduces the frozen false-pass condition: the auditor accepts chronology labels that contradict the raw interval bounds while aggregate counts stay unchanged.

At the final state refresh, open draft #7662 had advanced from the frozen commit to `a1cbc360d59ca90ceb6cc5cf2ca31be5e64c0414`. The exact Git blobs for `audit_a01.py`, `raw/A01.json`, `FREEZE.json`, and `CANDIDATE_SOURCE.py.txt` are unchanged between those commits, so this finding still applies to the current draft auditor and evidence inputs.

This is an audit-integrity finding against the saved-result checker in one draft #7662 artifact. It does not show that #7662's candidate projector is wrong on its test inputs, and it does not establish physical key timing, application consumption, useful game feedback, recovery efficacy, or live threat control.

## Checker audit trail

The first post-hoc independent checker is preserved as `independent_audit_v2.py` with `AUDIT_V2.stdout.txt` and `AUDIT_V2.exit.txt`. It returned `FAIL_AUDIT_V2` because its gate compared the whole recomputed error list to exactly four; the independent oracle correctly reported four chronology-label mismatches plus eight status/output consistency errors caused by the same two swapped rows in each sweep.

`independent_audit_v3.py` is a separately versioned post-hoc correction. It keeps the frozen decision rule focused on the four chronology-label mismatches, requires the baseline oracle to be clean and both original auditor runs to pass, and revalidates all v2 source/raw/output hashes and the exact mutation shape. It reports `PASS_REPRODUCED_AUDITOR_FALSE_PASS` in `AUDIT_V3.json`. Neither checker repeats the experiment.

## Verification and limits

- The test-first v2 raw-oracle tests pass 2/2.
- The v3 frozen-gate tests pass 2/2, including failed-auditor and wrong-mismatch-count controls.
- Python byte-compilation and `git diff --check` pass.
- The original #7662 auditor ran once per frozen arm; no retry or candidate run occurred.
- CPU-only synthetic JSON. No container, WSLc, GPU, game, model, GUI, X server, OS input, or shared allocation was used.
- Issue #59's current-main live run, per-key physical timing, independently useful feedback, bounded recovery and MAP01 exit gates remain open.
