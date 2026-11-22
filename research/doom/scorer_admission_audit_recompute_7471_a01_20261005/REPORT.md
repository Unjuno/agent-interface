# Scorer admission auditor false-pass check — A01

## Question and frozen decision rule

This additive, synthetic-only check asks whether the merged #7471 auditor can accept a changed raw sample history while the declared `expected` and `observed` fields remain unchanged. The freeze pins source commit `decefbd53240cdac21633e0d3e66c7e3bec76722`, exact source blobs and hashes, one mutation, and a no-retry rule. It changes only sample index 2's score in `bracketed_bounded_positive` from `1` to `0`.

The predeclared outcome requires the original audit to pass on baseline and mutation, and an independent raw-history reconstruction to disagree with the retained decision. If either condition failed, the finding would be held as not reproduced.

## Result

The one-shot experiment produced `FAIL_AUDITOR_ACCEPTS_RAW_MUTATION`: the merged auditor passed both inputs (exit code 0 with identical stdout hash), while the positive case recomputed as `ADMISSION_BRACKETED_PROGRESS` at baseline and `POST_CANCELLATION_COOCCURRENCE` after removing the positive score. The retained `observed.decision` stayed `ADMISSION_BRACKETED_PROGRESS`. This establishes one audit-integrity false pass for the tested raw mutation. It does not establish a runtime, causal, or recovery effect, and it does not characterize other possible mutations.

## Audit trail and checker repair

The first independent checker is preserved unchanged in `independent_audit.py`, `AUDIT.json`, `AUDIT.stdout.txt`, and `AUDIT.exit.txt`. It failed (`FAIL_AUDIT`, exit 1) because its verification harness read the wrong freeze keys (`source_sha256` instead of `frozen_sources[*].sha256`, and `score_after` instead of `mutation.to`). That was a checker schema error, not a failed or repeated experiment.

`independent_audit_v2.py` validates the saved freeze/source hashes, the exact single-field mutation, the preserved original auditor outputs and exit codes, and the recomputed decisions from both saved raw files. It records `PASS_REPRODUCED_AUDITOR_FALSE_PASS` in `AUDIT_V2.json`. It only re-audits the preserved files; the one-shot experiment was not rerun. `test_independent_audit_v2.py` also checks the reported false pass and rejects post-run sample tampering or a missing case row.

## Verification and bounds

- `python -m unittest -v test_independent_audit_v2.py` — 3 tests passed.
- `python independent_audit_v2.py` — passed against the preserved run.
- Python compile check and `git diff --check` are recorded in the PR validation.
- CPU/Python synthetic JSON only. No game, model, live input, GUI, GPU, container, WSLc, or shared allocation was used.
- This package does not alter the merged #7471 package or claim per-key physical timing, useful-feedback benefit, bounded live recovery, or causal attribution.
