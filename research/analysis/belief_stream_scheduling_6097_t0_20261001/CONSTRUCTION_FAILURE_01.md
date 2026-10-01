# Construction failure 01 — retained unchanged

The first un-frozen construction attempt is retained in `construction_raw.jsonl` and `construction_audit.json`. It is not a formal allocation and must not be described as a passing experiment.

- Host unittest began 2026-10-02 UTC+09 and was interrupted after observing two test failures and a prohibitively slow repeated exact replay. The interrupt is a construction interruption, not a scientific STOP.
- A one-shot pinned-container rerun of the same candidate completed: candidate 4.28 s, independent audit 3.45 s. Audit disposition was `FAIL_AUDIT` with `heldout_miss_improvement` and three unsupported-control fallback errors.
- Independent inspection found the auditor failed to apply the mode-switch transition after tick 2 when updating unobserved beliefs. The candidate also claimed a held-out weighted-miss improvement that the exact result did not show; cyclic and AoI tied, while the belief-value policy was slightly worse.
- `test_scheduler.py` repeats complete raw generation in `setUpClass` and then performs multiple full 4096-world replays for mutation tests. The host run exceeded 60 seconds and was interrupted; no claim of test-suite PASS is made.

Disposition: `FAIL_CONSTRUCTION_01`; preserve all files and hashes. Any corrected candidate/auditor is a new construction version. Do not overwrite these outputs or retroactively reinterpret this failure.

## Follow-up construction attempt

After adding mode-switch transition handling to candidate/auditor and relaxing only the preregistered superiority assertion to a non-worse-than-cyclic/AoI plus strict improvement over entropy criterion, the first corrected-container test invocation stopped before tests ran (`NameError: case_id` in the candidate's mode-switch belief update). No formal allocation was consumed. The invocation is preserved here; the source correction follows in the construction lineage and does not change the original failed raw files.
