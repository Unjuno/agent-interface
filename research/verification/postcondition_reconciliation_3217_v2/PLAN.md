# #3217 current-main / retained-artifact reconciliation plan

## H
The retained 90-row workflow artifact from run 35466506122 is reproducible from the unchanged current-main candidate source, and a separately implemented raw-only auditor can recompute every row without trusting candidate or historical-auditor verdicts.

## T
- Historical workflow run: 35466506122, head `6960809cdf9ccc2c2cda24ad84cab94c3cd2b4b6`, conclusion success.
- Artifact: 10590764445, ZIP SHA-256 `863177586ae3d686c05b2c150967a9c426ef8d460b86ae5b8fc9a0243954b728`.
- Publication-base main: `2df540489fb3f810a1cbd220d0761ca7ec1b23d0`.
- Current-main and workflow-head Git blobs match exactly for experiment.py, audit.py, Dockerfile, and workflow.
- Construction/provenance check: run exact current-main `experiment.py` then historical `audit.py` once in the provided Linux container, not as a Docker replication, and compare output bytes with the retained artifact.
- Formal audit: exactly one invocation of `independent_audit.py` over retained raw.json/audit.json. It imports neither candidate nor retained audit code.
- Six copied-evidence controls: missing row, duplicate identity, forged wrong-target PASS, changed target_observed, altered rich-agent-call count, changed source binding.

## D
`PASS_CURRENT_MAIN_ARTIFACT_RECONCILED_SCOPED` only if source/artifact bindings match; 90 unique rows are present; independent evidence reconstruction yields the exact candidate verdict/reason and shadow-call disposition on every row; no non-valid case is PASS; rich-agent counts are exactly 30/18/12; historical audit payload is internally consistent; and all six corruptions reject.

Source/evidence mismatch or candidate/auditor disagreement is FAIL. Missing evidence/execution capability is HOLD/STOP.

## C
This is reconciliation of one synthetic verifier contract. It does not overwrite historical #3048/#3070/#3173 outcomes. The historical audit is checked but is not treated as independent authority. The fresh construction run is CPython 3.13.5 in the provided Linux container and is not represented as the original Python 3.12 Docker environment.

## U
No fresh Docker/Xvfb allocation, model/provider call, live GUI action, task-effect generality, latency/token benefit, or production claim. The evidence package resolves source/artifact retrievability and row-level independent reconciliation only.
