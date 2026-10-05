# A01 formal failure record

The frozen candidate invocation completed successfully and wrote `formal_01/candidate.json`. The single frozen auditor invocation exited 1 and wrote `formal_01/audit.json` with gate `FAIL`.

The output shows both `whole_record` and `dependency_aware` matched the independent oracle in all six fixtures; all five frozen mutation controls were rejected; and the dependency-aware method used fewer recomputations. The auditor incorrectly included the intentionally weak `independent_field` comparator's expected stale-value counterexamples in its blocking `errors` list, so its final gate failed despite the method-scoped outcome being otherwise satisfied.

This is an auditor-gate defect, not a candidate or environment failure. The candidate and audit outputs are preserved byte-for-byte. Neither frozen invocation was retried. The gate repair is recorded under the additive A02 package; A01 remains a failed formal allocation.

Container: `docker.io/library/python@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3`, `linux/arm64`, OrbStack, `--network=none`, `--pull=never`.

Output SHA-256:

- candidate: `see SHA256SUMS`
- auditor: `see SHA256SUMS`
