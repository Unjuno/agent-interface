# Role-router online LoRA audit successor — Issue #5172

## H / T / D / C / U

- **H:** A corrected independent raw-only auditor can bind and reconstruct the complete per-arm training schedule, including `base_row_indices`, while rejecting missing, extra, reordered, duplicated, mutated, or digest-inconsistent schedules before any optimizer work is authorized.
- **T:** Successor allocation `needle-role-router-online-lora-audit-v2-20260928`; parent #4899 and draft PR #4906. Source lineage is PR #4906 head `30c4a4d867484b0f7c9687ee78de9f5a0e71d49c`; PR #4906 remains open/draft/unmerged. Branch `research/role-router-online-lora-audit-successor-20260928`; additive path `research/system1/needle_role_router_online_lora_audit_v2_20260928/`. No formal seeds assigned or frozen. Stage 0 is zero optimizer updates, no model fit, no query/timing workload. A fresh one-shot formal experiment would require a later source freeze, collision audit and exclusive CPU lease.
- **D:** No source/test execution is claimed yet. Intended Stage-0 disposition is `PASS_AUDIT_CONTRACT_CONSTRUCTION_SCOPED` only if valid fixtures are accepted, every registered corruption is rejected, and test instrumentation demonstrates that fit/update entrypoints remain uncalled.
- **C:** Prior #4899 raw/audit show all three errors are missing `base_row_indices:digest`; all 192 checkpoints otherwise replayed. Separately batched arms must be replayed independently—do not assert equality across distinct batch schedules. Auditor and fixture must not share the same digest-construction helper. Queue #5085 currently records an owner-unidentified OpenFOAM container and CPU work; no local or OrbStack container may be started without explicit current allocation ownership/release.
- **U:** No scientific quality, skill retention, online learning, natural-language role-routing, end-to-end timing, product/runtime or action-authority conclusion.

## Stage-0 acceptance matrix

| Case | Expected |
|---|---|
| Canonical valid schedule + exact digest and full arm/seed identity | accept |
| Missing `base_row_indices` key or digest | reject |
| Extra/unrecognized schedule digest key | reject |
| Reordered or duplicate indices | reject |
| Single index mutation with stale digest | reject |
| Digest mutation with unchanged schedule | reject |
| Duplicate JSON object keys / noncanonical or non-finite encoding | reject |
| Arm/seed/allocation mismatch | reject |
| Any runner fit/update hook reached | test failure and STOP |

Use small deterministic synthetic fixtures only. The auditor must rebuild the expected schedule from frozen inputs and independently canonicalize/hash observed rows; it may not import the producer's hashing helper. Report the exact tested blobs, invocation, stdout/stderr hashes, exit code and number of optimizer calls. Preserve every failure. Do not consume formal seeds at Stage 0.

## Formal-stage guard

Do not run the prior three seeds (736211/736311/736411) or construction seed (736014). Fresh formal seeds have not been allocated. Do not interpret the prior descriptive 1/1 A/B as a PASS; #4899 remains `HOLD_AUDIT_INTEGRITY` and also records one preregistered A-retention comparison miss.