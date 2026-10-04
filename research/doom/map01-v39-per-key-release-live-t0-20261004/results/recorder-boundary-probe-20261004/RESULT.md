# Candidate recorder-boundary construction probe — 2026-10-04

**Disposition: `PASS_FAIL_CLOSED_RECORDER_CONSTRUCTION_ONLY`.** A new main-level regression is red on PR #7386's exact prior head and green after the repair. Candidate/auditor construction tests pass 13/13; byte-compilation and `git diff --check` pass.

## H / T / D / C / U

- **H:** if `initial_candidate_record()` rejects an incomplete network receipt after `candidate_started.json` has been written, `main()` still returns a bounded failure and writes an incomplete `candidate.json`.
- **T:** inject a one-field receipt from a stubbed `verify_frozen()` into `candidate.main()` with a temporary output directory. Run the same test against baseline `341c333f33908852d3ff377c79d5100bb0e1ee91` and the repaired source.
- **D:** PASS only if the baseline test fails through the uncaught `STOP_NETWORK_RECEIPT_INCOMPLETE`, while the fixed code returns exit 2, writes `candidate.json` with `candidate_completed=false` and the exception in `issues`, and creates no X11 display.
- **C:** this is adversarial evidence handling. The production verifier is expected to return its complete receipt; the probe does not show that the actual verifier produces a malformed receipt.
- **U:** no X11, physical input, game, model, container, live candidate, matched condition, task feedback, recovery measurement, or scientific outcome was tested. This follow-up changes candidate source and does not authorize rerunning the previously stopped/consumed T0; any future candidate requires a new freeze and valid allocation.

## Exact execution

- Baseline source: PR #7386 head `341c333f33908852d3ff377c79d5100bb0e1ee91`.
- Regression: `python -B -m unittest test_candidate.CandidateNetworkReceiptTests.test_incomplete_network_receipt_is_retained_by_main -v`; baseline exit 1 as expected.
- Candidate/auditor suite, from this package directory: `python -B -m unittest test_candidate test_audit -v`; exit 0, 13 tests.
- Static checks: `python -B -m py_compile candidate.py test_candidate.py audit.py test_audit.py` and `git diff --check`; both exit 0.
- Environment: Windows AMD64, CPython 3.11.9.

Full baseline and fixed outputs are retained in `BASELINE_RED.json` and `CONSTRUCTION.txt`. SHA-256 identities for the changed candidate/test sources and raw outputs are in `SHA256SUMS.txt`.
