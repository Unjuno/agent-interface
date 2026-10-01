# Endpoint-lineage auditor coverage successor

This additive audit follows PR #5755 without changing its fixture, candidate
output, auditor, PASS, or hashes. It tests what the retained independent audit
actually checks and supplies a separate exact-rational auditor for every
reported numeric field in the six frozen synthetic cases.

## Reproduce

From the repository root:

```sh
cd research/analysis/endpoint_lineage_audit_coverage_v1
shasum -a 256 -c SHA256SUMS
python3 endpoint_audit_coverage_probe.py
python3 endpoint_lineage_audit_complete.py
```

The coverage probe fetches the predecessor fixture, candidate stdout, and v1
auditor from immutable commit `68a4a983118fbbfaecf875c44fe04fadff3b4bd9`,
checks their frozen SHA-256 values, and runs only copied candidate-output JSON
and isolated subprocesses in temporary directories. It does not rerun the
candidate reducer. It first demonstrates v1 accepting two preregistered,
well-formed but incorrect fields. It then runs the successor auditor once on
the unchanged output and once for each of the 38 numeric-string fields after
an isolated `+1` mutation. Every mutated run must fail specifically with an
`AssertionError`; crashes do not count as successful rejection.

The standalone auditor can also be run against the adjacent frozen fixture and
candidate-output copies. During the probe it is staged under the temporary name
`audit_complete.py`; the retained canonical filename is
`endpoint_lineage_audit_complete.py`.

## Scope

`PASS_ENDPOINT_LINEAGE_AUDIT_COVERAGE_SCOPED` establishes only that (a) the v1
auditor omits exact assertions for `naive_sum` and per-segment interval values,
and (b) this separately authored v2 checker recomputes all displayed fields
for this fixed fixture and rejects isolated mutations to its 38 numeric-string
values. Exact finite rational arithmetic only. No calibrated clock model,
real endpoint validity, live latency, MAP01/runtime effect, probability,
safety, or product claim follows.

No container was used: the parent task already recorded Docker Desktop as
unresponsive with unrelated Created containers. This deterministic local
stdlib-only audit used temporary directories and fresh Python subprocesses; it
did not inspect or modify Docker or shared runtime state.
