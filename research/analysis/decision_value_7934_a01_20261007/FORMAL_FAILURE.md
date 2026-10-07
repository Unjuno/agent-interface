# A01 formal launch failure — terminal STOP

Allocation: `7934-DECISION-VALUE-ACQUISITION-A01-20261007`  
Issue: #7934  
Disposition: **STOP_OUTPUT_PATH_MISSING**; this is an execution/setup failure, not a scientific result.

The frozen protocol required the candidate output at
`results/formal01/candidate.raw.json`. The one authorized candidate invocation
was made from this package directory at `2026-10-07 13:04:52 UTC`:

```text
python3 -B candidate.py fixtures/candidate_model.json results/formal01/candidate.raw.json
```

It exited 1 with `FileNotFoundError` because `results/formal01/` had not been
created. No candidate output was produced. The directory-preparation launcher
had incorrectly gated on branch `HEAD == main`; the frozen commit is a child of
main, so the gate prevented its `mkdir`. This is a researcher/launcher setup
error, not an algorithm failure.

Formal invocation counts are candidate 1, scorer 0, auditor 0; retries 0.
The exact allocation is terminal under the preregistered one-shot rule. Do not
rerun any A01 formal command. No performance, calibration, or hypothesis claim
is supported. Any follow-up must use a separately preregistered successor
allocation and a new additive package/path.

The frozen source/input identity remains in `FREEZE.json` and commit
`7648ebc67cfa7634f282118d560648d80f456bb7`; base main was
`8c8b37424fdb43482412240868574813fae46c2e`. Runtime preflight and the no-
container-claim boundary are recorded in `PREFLIGHT.json` and `PROTOCOL.md`.

## Output record

| Role | Invocations | Exit | Output |
|---|---:|---:|---|
| Candidate | 1 | 1 | none; parent directory missing |
| Scorer | 0 | — | not run |
| Independent auditor | 0 | — | not run |

