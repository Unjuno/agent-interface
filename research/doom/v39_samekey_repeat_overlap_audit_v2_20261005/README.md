# V39 repeated same-key overlap audit v2

This additive read-only audit tightens the `HOLD_NON_BIJECTIVE` boundary from
PR #7917. The original candidate, `FREEZE.json`, `RAW.json`, `audit.py`, and
`AUDIT.json` in that PR's tree are unchanged. This package copies the original
freeze and raw inputs byte-for-byte from PR head
`6991ec9e6d75907da626597bed0dd16e982e8410`, records their Git blob and SHA-256
identities, and tests only the overlap-case decision predicates. No candidate
or formal experiment is rerun.

## H / T / D / C / U

- **H:** A raw-only auditor can retain the observed two-admission/one-release
  overlap as `HOLD_NON_BIJECTIVE` while rejecting a release receipt that occurs
  before either admission acknowledgement and rejecting cross-context
  admissions. The event rows must share ID/step/token/owner; the nested owner
  receipt must share owner/token, which are the fields it actually records.
  Malformed event rows fail closed.
- **T:** Run one read-only audit over the immutable copied `RAW.json`; then run
  four in-memory corruption controls for late acknowledgements, foreign
  admission context, foreign release context, and malformed event-row shape.
  Do not modify the copied inputs or invoke the candidate.
- **D:** The unmodified overlap must pass integrity checks with a
  `HOLD_NON_BIJECTIVE` disposition. Every corruption must fail the audit with
  the corresponding predicate error. Any provenance mismatch is a failure.
- **C:** The input is a retained fake-X/display trace; the audit verifies raw
  chronology and identity fields only.
- **U:** This does not revalidate the selected source closure or candidate
  execution and does not establish physical key state, real X delivery,
  application effect, useful feedback, latency, threat control, recovery, or a
  MAP01 outcome.

## Reproduction

From the repository root:

```powershell
python -B research/doom/v39_samekey_repeat_overlap_audit_v2_20261005/audit_v2.py
python -B -m unittest research.doom.v39_samekey_repeat_overlap_audit_v2_20261005.test_audit_v2 -v
python -O -B -m unittest research.doom.v39_samekey_repeat_overlap_audit_v2_20261005.test_audit_v2 -v
```

The read-only audit and mutation-control result are recorded in `FREEZE.json`
and `results/`; `SHA256SUMS.txt` binds the inputs, executable sources, and
outputs.
The candidate and original audit outcomes remain historical evidence. This
audit is a versioned supplemental check and does not replace them.
