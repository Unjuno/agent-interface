# T5 execution record

- Candidate invocations: two identical deterministic executions (preregistered one-invocation gate inadvertently violated); the first JSON is retained, and the second displayed matching JSON but was not saved separately. No RNG or tuning.
- Engine/image/command and exact model: see `REPORT.md`.
- Candidate output: `raw/formal.json`.
- Independent audit v1: failed only its `1` versus `1/1` total-mass string comparison; preserved at `raw/audit.json`.
- Audit v2: exact rational comparison corrected; PASS at `raw/audit_v2.json`.
- Corruption controls: 4/4 rejected; details at `raw/corruption_controls.json`.
- Result scope: synthetic null with independent time vectors and cross-branch shared/private dependence; no product or semantic-verification claim.
