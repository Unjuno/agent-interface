# Issue #5404 — typed resumption packet T0

**Disposition: `PASS_TYPED_RESUMPTION_SCOPED`.** In one frozen OrbStack run, the typed-packet policy had zero unsafe admissions across 50 interruption/fault/idempotency scenarios. The separate raw-only audit independently reconstructed all 150 policy outcomes, confirmed all 48 non-benign invalidation/receipt cases were detected, and rejected four corruption controls. On the two benign pre-action pause cases, the packet took 2 synthetic recovery steps versus 7 for full replay. Opaque summary produced 45 unsafe admissions in the same fixture. This is a deterministic contract result, not a live interruption or runtime claim.

## H / T / D / C / U

- **H:** A typed packet binding execution/authority generation, evidence/target identity, and last-action receipt state can avoid unsafe stale continuation and duplicate non-idempotent effects while using fewer recovery steps than full replay on benign pauses. An opaque prose-like summary fails at least one injected boundary.
- **T:** Five interruption points × five fault conditions × two idempotency classes = 50 scenarios; compare `OPAQUE_SUMMARY`, `FULL_REPLAY`, and `TYPED_PACKET` (150 outcomes). Rebuild every expected outcome in a separate raw-only auditor. No GUI/model/network/task input.
- **D:** PASS if all rows reconcile, packet unsafe admissions are zero, every non-benign invalidation/receipt case is detected, revoked authority/unaccepted handoff fail closed, committed effects are reconciled rather than repeated, benign packet step cost is lower than full replay, and audit/mutation controls pass. Unsafe packet admission or duplicate non-idempotent effect is FAIL; provenance/audit failure is STOP.
- **C:** The oracle has complete event/effect knowledge and perfect receipt lookup; full replay cost is fixed; re-observation/re-grounding identifies the same semantic target except revoked authority and unaccepted handoff. These are synthetic assumptions.
- **U:** Step counts are not wall time or tokens. No human interruption timing, real GUI drift, hidden effects, crash persistence, event-store completeness, task-quality, runtime/product, or production-safety claim. A packet cannot prove the external world remained unchanged.

## Result

- Allocation: `typed-resumption-5404-t0-orbstack-20260930-01`; one formal invocation, no rerun.
- Complete denominator: 50 scenarios, 150 policy outcomes.
- `TYPED_PACKET`: unsafe admissions 0; 48/48 non-benign stale/authority/geometry/handoff/receipt conditions detected; committed or unknown effects reconciled without resending.
- `FULL_REPLAY`: unsafe admissions 0 in this model; benign pre-action interruption costs 7 steps.
- `OPAQUE_SUMMARY`: 45 unsafe admissions in the fixture; it does not validate invalidation predicates or action receipt state.
- `TYPED_PACKET`: benign pre-action interruption costs 2 steps. This is an operation-count comparison, not latency.
- Independent audit: `PASS_TYPED_RESUMPTION_SCOPED`, 0 errors, mutation controls 4/4 rejected.
- Raw SHA-256: `4a5cd7869d2824c293d418f968403b0b8ab65e977268982b44a2a9ebb9860b35`.
- Audit JSON SHA-256: `010c09ed7043567eb9cae89c4d4a107a4b02f25b831b4108e70b3fd0b3fcb741`.

## Provenance and artifacts

Source freeze/main: `e81cbac968752791678d22a4de3f2d276497d614`, `2026-09-30T10:38:13Z`. Formal run: `10:39:20Z`; separate audit: `10:39:27Z`. Pinned Python 3.12 slim image, OrbStack, Docker Engine 29.4.0, Linux/arm64; network none, read-only root/source, 1 CPU, 256 MiB, 64 pids, all capabilities dropped, no-new-privileges. Exact commands and stdout are in [`EXECUTION.md`](EXECUTION.md); frozen hashes are in [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md). Container IDs were not recorded because `--rm` was used without a CID file.

- Candidate/oracle: [`experiment.py`](experiment.py)
- Separate raw-only auditor: [`audit.py`](audit.py)
- Scenario matrix and policy outcomes: [`raw/formal.jsonl`](raw/formal.jsonl)
- Independent audit summary: [`raw/audit.json`](raw/audit.json)
- Preregistration and issue: [`PLAN.md`](PLAN.md), [Issue #5404](https://github.com/Unjuno/agent-interface/issues/5404)

The results are limited to this deterministic state machine. `FULL_REPLAY` is a specified synthetic baseline, and the 45 opaque-summary failures are fixture outcomes, not an estimate of real-world failure prevalence. No runtime component was changed.
