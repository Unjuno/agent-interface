# A03 one-shot run log

- Allocation: `PHASE-CONTROL-DELAYS-8668-T0-A03-20261009`.
- Frozen base main: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`.
- Freeze commit: `9132f99c3834576a2a7727f39a8b518d9a8edd58`.
- Freeze SHA-256: `456a191bbca3ae8e4052570969234368f463217058ef2d8401574b075e77e19d`.
- Pre-run state: Issue #8668 open and unassigned; A01 PR #8698 and A02 PR #8745 remain separate; A03 branch SHA matched the freeze commit. Construction tests passed 12/12 normal and 12/12 optimized. Formal candidate/auditor invocation counts were 0 before launch.
- Container preflight: OrbStack 29.4.0 `docker images` stopped before listing images on content blob `c496fe61337ebef922bbd35d18f3a4d0f30c1524c0fc08fbcfff7b5c68d54643` (`operation not supported`). No container was started. The selected host sandbox had already returned `EPERM` on a loopback attempt.

## Formal candidate

Command, invoked once:

```text
/usr/bin/sandbox-exec -p '(version 1) (deny network*) (allow default)' python3 -B candidate.py > run-01/candidate.json 2> run-01/candidate.stderr
```

Exit 0; retries 0; stdout 281,349 bytes, SHA-256 `95c248d033eda47a62be118f1594a4f8f06521abf365bdc433c2e7d08fb4e541`; stderr empty.

## Independent raw-only auditor

Command, invoked once after candidate exit 0:

```text
/usr/bin/sandbox-exec -p '(version 1) (deny network*) (allow default)' python3 -B auditor.py < run-01/candidate.json > run-01/audit.json 2> run-01/auditor.stderr
```

Exit 0; retries 0; stdout 506 bytes, SHA-256 `39ad5f91624ef74a028029aa3c1af287196d98815b1e516bfef917f6a369a268`; stderr empty. Audit gate `PASS_METHOD_SCOPED`, rows 317/317, errors `[]`, mutations rejected 9/9. Raw-derived results and the audit's decision-label nuance are described in `REPORT.md` and the immutable reclassification record.

The report and decision-label reclassification were written after both one-shot outputs. The candidate and original auditor were not rerun. Frozen source hashes still match `FREEZE.json`.
