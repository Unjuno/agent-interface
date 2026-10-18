# Candidate recorder-boundary construction probe — 2026-10-04

**Disposition:** `PASS_FAIL_CLOSED_RECORDER_CONSTRUCTION_ONLY`.

**H:** If `initial_candidate_record()` rejects an incomplete network receipt
after `candidate_started.json` is written, `main()` should still return a
bounded failure and write an incomplete `candidate.json`.

**T:** A stubbed `verify_frozen()` supplied an incomplete receipt to
`candidate.main()` with a temporary output directory. The same regression ran
against baseline #7386 head `341c333f33908852d3ff377c79d5100bb0e1ee91` and the
repaired source.

**D:** The baseline regression exited 1 with the expected uncaught
`STOP_NETWORK_RECEIPT_INCOMPLETE`. After repair, it returned exit 2 and wrote
`candidate.json` with `candidate_completed=false` and the exception in
`issues`; no X11 display was created. Candidate/auditor tests passed 13/13;
byte-compilation and `git diff --check` passed.

**C:** This is adversarial evidence handling. The production verifier is
expected to return a complete receipt; the probe does not show that it
produces a malformed receipt.

**U:** No X11, physical input, game, model, container, live candidate, matched
condition, task feedback, recovery measurement, or scientific outcome was
tested. The source change does not authorize rerunning the previously
stopped/consumed T0; any future candidate requires a new freeze and valid
allocation.

## Execution record

- Baseline regression:
  `python -B -m unittest test_candidate.CandidateNetworkReceiptTests.test_incomplete_network_receipt_is_retained_by_main -v`
  — expected RED, exit 1.
- Candidate/auditor suite:
  `python -B -m unittest test_candidate test_audit -v` — PASS, 13 tests.
- Static checks: `python -B -m py_compile candidate.py test_candidate.py audit.py test_audit.py`
  and `git diff --check` — exit 0.
- Environment: Windows AMD64, CPython 3.11.9.

The exact original outputs and their hashes are anchored by the PR #7414
source commit in `SOURCE_PROVENANCE.md`. This rescue record does not rerun or
replace those outputs.
