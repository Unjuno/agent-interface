# Issue #8574 T0 A01 — execution record

- Frozen base: `c995efeca4349353e1f5e13cd1b8aba29088b632`.
- Frozen experiment commit: `e977eef3cd4a5e616cb84da3f21fbe16444682dc`.
- Allocation: `8574-T0-A01-20261009`.
- Runtime recorded at freeze: Python 3.14.5 on macOS 27.0.1 arm64.
- Review assignment: six first-pass candidate reviews, two per arm. Order A: RV-17 checklist, RV-62 freeform, RV-04 perspective. Reverse order B: RV-39 checklist, RV-28 freeform, RV-75 perspective. Each reviewer assessed all 16 cases once. No candidate output was retried.
- Adjudication: one separate blind adjudicator, one response covering 79 findings. It received the blind case packets and findings without prompt, arm mapping, or gold labels.
- Audit: one raw-only audit invocation after adjudication and gold unsealing.
- Candidate invocations: 6; adjudicator invocations: 1; raw auditor invocations: 1; retries: 0.

Commands executed from the package directory:

```sh
python3 audit.py
python3 -m unittest discover -s . -p 'test_audit.py' -v
python3 -O -m unittest discover -s . -p 'test_audit.py' -v
```

Observed audit output: `NO_INCREMENTAL_VALUE_SCOPED`, 16 cases, 6 reviewers, 79 adjudications, zero errors, zero unsupported additions on clean controls, and zero ambiguity failures. Both normal and optimized test runs passed 3/3 tests.

The exact raw review responses are in `results/raw_review_RV-*.json`; the blind adjudication is `results/adjudicated_blind.json`. The arm assignment and gold inventory are retained for audit reproducibility after all blind review was complete. Their prospective hashes, along with hashes for frozen inputs, are in `FREEZE.json`; execution artifact hashes are in `results/ARTIFACT_SHA256SUMS.txt`.

No container was used because the frozen T0 calls for review of authored source/verification text only and no runtime behavior. This is not a live GUI or product experiment.
