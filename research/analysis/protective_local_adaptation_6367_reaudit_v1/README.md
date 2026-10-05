# Issue #6367 post-review disposition re-audit

This additive audit answers one code-review finding against the frozen T0
result: the original auditor reconstructed per-case statuses but did not
reconstruct the report's top-level `decision` or
`mechanism_attribution_eligible` fields.

## H/T/D/C/U

- **H:** A report with a safety-violation event must not pass independent audit
  if its top-level decision is changed to `DESCRIPTIVE_ALL_OFFER_TOTAL` or its
  mechanism-attribution flag is changed to true.
- **T:** Recompute the top-level precedence directly from frozen scheduled
  offers and raw events, then compare both report fields. Run this against the
  retained T0 artifacts and two deliberate report mutations. Do not rerun the
  candidate or original auditor invocation.
- **D:** Record exact input hashes and the supplemental audit output here.
- **C:** The original frozen T0 inputs, source, candidate result, and original
audit output remain unchanged. The corrected check is a successor audit, not
a replacement claim about the original invocation.

The regression suite also reproduces the original auditor's false PASS when
both top-level fields are mutated, then confirms the successor audit rejects
that same report.
- **U:** This qualifies only report-disposition consistency for the finite
  synthetic method fixture. It does not establish live-control safety,
  efficacy, generality, or container-level behavior.

Run from this directory with:

```sh
python -m unittest -v test_audit_top_level
python audit_top_level.py ../protective_local_adaptation_6367_t0_20261004/fixture.json ../protective_local_adaptation_6367_t0_20261004/events.json ../protective_local_adaptation_6367_t0_20261004/out/CANDIDATE.json
```

The frozen candidate/auditor invocations are not repeated. The test reads the
previously retained output and adds mutations only in memory.
