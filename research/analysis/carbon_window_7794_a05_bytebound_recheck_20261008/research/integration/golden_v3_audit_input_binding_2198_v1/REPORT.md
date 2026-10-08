# Golden v3 schema audit input-binding controls (#2198 / #3249)

## Result

**`FAIL_AUDITOR_INPUT_BINDING_SCOPED`** — the checked-in #2198 `audit.py` is not bound to the schema/result artifacts it purports to reconcile. Its source has no file reads, and all six isolated artifact controls returned byte-for-byte identical stdout, exit 0, and the same hardcoded digest.

**`HOLD_GOLDEN_V3_SCHEMA_SOURCE_EVIDENCE_INCOMPLETE`** — an independent reconstruction from frozen raw JSON finds 7 of 9 required contract fields absent, 1 present but value-contradictory (`schema`), and only `usage` present. This field check does not establish lineage or any auditable derivation. It does not change the prior HOLD.

## Scope and source freeze

- Governing Issue: [#2198](https://github.com/Unjuno/agent-interface/issues/2198); closure-audit requirements: [#3249](https://github.com/Unjuno/agent-interface/issues/3249).
- Repository commit: `eb3c8d108b8ddd090e5e81a22c7d5db9c367552c` (`main` at experiment start; `git ls-remote origin refs/heads/main` agreed).
- Before publication, main advanced to `a081e5d36e8298129f83bf22214d18dfa9e7717a`; schema/report/audit Git blob identities below were re-read unchanged at that current main, and the Docker controls were rerun with that commit as `SOURCE_COMMIT`.
- Schema: `research/integration/golden_v3_result_schema_2186_v1/schema.json`; Git blob `7fe3ad10ab69b0d8786d17ca854e65f90efd213b`; SHA-256 `c91c6994d5dab017432743b937a31140837790c5c22b5cf758722f8c4d14197d`.
- Exact report: `runtime/results/golden-desktop-app-server-v3-live-01/golden-report.json`; Git blob `e168a9bdc84fc6b807f4e90806ec7c501da89689`; SHA-256 `ea71c2370afeabfab6d39b058bb628d0ea78412f702d2f87982b6c64f579761c`.
- Candidate audit: `research/integration/golden_v3_schema_reconciliation_2198_v1/audit.py`; Git blob `e4e683951a69ced162713a1b54b2b467f8800e28`; SHA-256 `45abe851521c4ab274f161bffa6c2dcff1292e50363f485e20d36a86a5c95f59`.

## H/T/D/C/U

- **H — Hypothesis:** the candidate audit decision is invariant to schema/report evidence because it hardcodes field classifications instead of loading the artifacts.
- **T — Test:** run the unchanged candidate script in fresh isolated directories with unaltered files, no files, a renamed report field, prose-only field claims, a synthetic schema-v1 result, and a mutated schema identity. Separately parse exact current-main JSON bytes and independently reconstruct all required-field presence and schema-const agreement. Run raw-byte auditor corruption controls.
- **D — Decision:** candidate auditor integrity gate passes only if it reads supplied evidence and responds to corruption controls; otherwise scoped FAIL. Schema reconciliation passes only if all required fields have direct emitted evidence or auditable derivation; missing/contradictory evidence means HOLD. STOP only if frozen source cannot be recovered.
- **C — Controls/constraints:** six candidate controls; independent controls for renamed fields, prose-only claims, schema-required-field injection, synthetic valid result, contradictory schema identity, and unaltered source. No runtime, adapter, model, GUI, or input changes. No claim beyond JSON field presence/value. The original issue asked for no Docker, but deterministic work was nevertheless run locally in Docker Desktop (`python:3.12-slim`, Python 3.12.14); no shared project GPU/GUI slot used.
- **U — Unknowns:** no direct emitted provenance for absent fields; no lineage proof; this does not reevaluate the original desktop task, its independent evaluator, efficacy, latency, production readiness, or adapter behavior.

## Reproduction

From repository root, using Docker Desktop:

```powershell
$env:SOURCE_COMMIT = (git rev-parse HEAD)
New-Item -ItemType Directory -Force -Path "$((Get-Location).Path)/research/integration/golden_v3_audit_input_binding_2198_v1/evidence" | Out-Null
docker run --rm --pull=never `
  --mount "type=bind,source=$((Get-Location).Path),target=/repo,readonly" `
  --mount "type=bind,source=$((Get-Location).Path)/research/integration/golden_v3_audit_input_binding_2198_v1/evidence,target=/evidence" `
  --workdir /repo `
  --env "SOURCE_COMMIT=$env:SOURCE_COMMIT" `
  --env OUTPUT_DIR=/evidence `
  python:3.12-slim python research/integration/golden_v3_audit_input_binding_2198_v1/binding_experiment.py
Copy-Item research/integration/golden_v3_audit_input_binding_2198_v1/evidence/RESULT.json research/integration/golden_v3_audit_input_binding_2198_v1/RESULT.json -Force
```

The experiment script writes its machine result to `/evidence/RESULT.json` on a separately mounted host evidence directory and prints the same JSON to stdout. A byte-identical copy is retained as `RESULT.json` alongside this report. Independent audit entry point: `independent_audit.py`.

## Evidence

The candidate's AST contains no file-read call. With six cases (including missing artifacts and a valid synthetic result), every run exited 0 and emitted the same:

```json
{"adapter":0,"decision":"HOLD_PROPOSED_SCHEMA_NOT_SOURCE_BACKED","digest":"e69dcfc9cc5642bca6695d10b2cfbdc628663f498b8c014242704219593f3c26","fields":9,"runtime":0,"unverified":["program_completed","task_success","status","partial_effects"]}
```

The independent raw JSON reconstruction reports `ABSENT=7`, `EMITTED_VALUE_CONTRADICTION=1`, `EMITTED=1`. Corruption controls must retain HOLD for field removal/renaming, prose-only claims, injected requirements, and contradictory identity; a synthetic object satisfying the proposed schema is a positive control for required-field-presence mechanics only, not for provenance/source reconciliation. That synthetic control is not current-main evidence and cannot close the HOLD.

The retained raw result contains a separate `independent_evaluation.success=true`, six exact counts, and per-task `exact_submission=true`/`releases_verified=true`. These are real fields in that report, but they do not supply the distinct proposed required keys or prove a source-backed mapping to them.

## Validation and limitations

- `python -m py_compile .../independent_audit.py .../binding_experiment.py` — PASS.
- Docker Desktop reproduction — PASS after retaining four setup failures: root-resolution path off by one, missing `git` in the minimal image, output path on read-only mount, and independent-audit path/artifact-location mismatch. Each was corrected; no silent retry or source artifact substitution. Final full run passes all corruption controls.
- `git diff --check` — PASS.
- No PR checks yet; PR not yet opened.

No adapter implementation or promotion follows. Candidate-audit scoped FAIL and contract HOLD are separate decisions; neither asserts the underlying desktop demonstration failed.
