# Research Preview readiness audit — 2026-09-19

This is a release decision record for Issue #58. It indexes frozen evidence on
main and keeps scoped research passes separate from release claims.

## Decision

**HOLD_RESEARCH_PREVIEW_NOT_READY**

The repository has three scoped passes, but the complete Research Preview
gate set is not closed. The current source also does not emit the result
provenance required by the golden desktop v3 contract, and no source-backed
CLI adapter mapping exists yet.

## Gate matrix

| Gate | Disposition | Evidence |
| --- | --- | --- |
| Golden desktop workflow | HOLD | Installability, checksum, and a reproducible packaged run are unverified. |
| Reconstructable benchmark numbers | PASS_SCOPED | Frozen receipts and validator evidence are indexed. |
| README and operator instructions | PASS_SCOPED | Main documentation is present; release packaging remains unverified. |
| Architecture and authority boundaries | PASS_SCOPED | Scoped audits preserve zero authority escalation. |
| DOOM showcase | HOLD | No supported reproducible video/evidence bundle is pinned. |
| Runnable package | HOLD | Package, checksum, and install smoke are unverified. |
| Supported OS/backend | HOLD | Supported backend matrix is not proven. |
| Smoke/self-check | HOLD | Release smoke artifact is not pinned. |
| Recovery/observation integration | HOLD | O3/O4/recovery/runtime consolidation is incomplete. |

## Secondary integration evidence

| Evidence | Disposition | Why it remains a hold |
| --- | --- | --- |
| Golden v3 emitted result provenance | HOLD_FIELD_PROVENANCE_INCOMPLETE | PR #2236 found an emitted v2 report boundary, but source-backed `program_completed`, `task_success`, `partial_effects`, normalized status, and cleanup error fields are absent. |
| CLI adapter contract | HOLD_ADAPTER_CONTRACT_NOT_SOURCE_BACKED | PR #2215 mapped current CLI statuses (`returned`, `backend_unavailable`, `runtime_failed`) and confirmed the frozen golden statuses are not emitted by current source. |

## H/T/D/C/U

- **H:** Keep release readiness machine-readable and prevent scoped PASS claims from becoming release claims.
- **T:** Freeze main evidence, include the adapter/provenance holds, and evaluate Issue #58 only after the remaining gates have source-backed artifacts.
- **D:** HOLD until the nine gates and the two secondary integration contracts are resolved.
- **C:** This audit is additive index/decision evidence. It makes no GUI, model, network, Docker, package, adapter, or authority-escalation claim.
- **U:** Installability, checksum, golden execution, supported backend, DOOM evidence, smoke, recovery/runtime consolidation, and source-backed result provenance remain unverified.

## Next bounded successor

A fresh release-preparation successor must produce a source-backed golden desktop result schema, a real CLI adapter mapping, and packaged install/smoke evidence before changing this disposition.
