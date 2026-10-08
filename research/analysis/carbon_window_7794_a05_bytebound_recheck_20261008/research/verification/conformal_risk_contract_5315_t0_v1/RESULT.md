# Issue #5315 — conformal risk contract boundary T0

**Overall: FAIL the intended certificate-checker hypothesis; preserve as a
negative result.** The formal output remains immutable at
`evidence/formal01/RESULT.json` (SHA-256
`8ed0551fac8cc5826fcdcdea475d68559c2555655d811554d61f03b48afae2bf`). See
[the post-hoc review](POSTHOC_REVIEW.md) for the digest-binding defect.

## Executed result

Source was frozen at commit `514693c9977a8055374e5a49b1dc91fc6e4b20e0`,
based on main `70b69b47845b35afde59c2a5f0b56c6f906c6904`. Python 3.14.5,
standard library only. Exact command:

```sh
python3 -B run.py --out evidence/formal01/RESULT.json
```

Exit 0; 5 deterministic arms and 5 corruption controls. The independent raw
auditor initially stopped with `STOP_AUDIT_EXPECTATION_MISMATCH` because it
expected UI version rejection before population rejection. The candidate's
documented check order returned population mismatch first. The initial STOP
is in `evidence/formal01/AUDIT_STOP_01.json`; an audit-only correction then
passed. It did not rerun the formal simulator or mutate its raw result.

Calibration had n=199, 8 errors, B=1, alpha=0.05. The exact expression
`n/(n+1) * Rhat + B/(n+1)` is 0.045. In the IID fixture, 40 of 1,000 tasks
emit a high-score singleton and all 40 are wrong: population loss 0.04,
conditional selected risk 1.00. The plain CRC contract is allowed only for
marginal population risk; singleton output remains UNCERTAIN and the set-valued
path remains `{PASS,FAIL}`. Four temporal/UI/family/adaptive rows are rejected
for stale or mismatched applicability. The fixed checklist false-pass counts
in these fixtures are 0, 5, 10, 5, and 20; these are specified fixture values,
not measured performance.

## Validation and limits

- Construction: `python3 -m unittest -v test_contract` — 3 passed;
  `py_compile` and `git diff --check` passed.
- Corrected independent audit: PASS for arithmetic, the marginal/conditional
  counterexample, shift rejection, and 5/5 declared controls.
- Post-hoc digest mutation: **FAIL**; a changed non-empty digest was accepted.
  Therefore do not treat the checker or its allowed marginal claim as a
  trustworthy certificate implementation.
- Host-only deterministic fixture; the shared Docker/CPU coordination gate
  (#5085) did not grant this task a container slot. No container was launched.
- No representative calibration corpus, statistical resampling, model, GUI,
  task-effect, SCRC algorithm, runtime, production, or causal claim.

Raw result, first audit STOP, corrected audit, and post-hoc review are separate
files; none overwrites the prior evidence.
