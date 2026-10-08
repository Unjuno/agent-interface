# #1858 real-source role adapter registry

Decision: **PASS_REAL_SOURCE_ROLE_ADAPTER_REGISTRY_SCOPED**.

## Result
A source-type registry normalized retained real evidence into the role/lifetime contract established by #1823/#1835/#1848.

| retained source | rows | normalized role | scope | storage |
|---|---:|---|---|---|
| #1639 focus generation + observation identity | 5 | PREPARED_REUSABLE_VERSIONED | FOCUS_OBSERVATION_CURRENTNESS | PERSIST_DEPENDENCY |
| Chromium target-handle check | 2 | FRESH_COMMIT_BOUND_CURRENT | TARGET_HANDLE_CURRENTNESS | EPHEMERAL_ONLY |

Formal outcome:
- emitted receipts: **7**
- rejected negative controls: **5**
- persistent target-handle receipts: **0**
- focus current controls: STABLE/PAINT_ONLY TRUE; FOCUS_ABA/FOCUS_CHANGE/IDENTITY_MISMATCH FALSE
- Chromium task3 `persistent_a_field@58`: TRUE
- Chromium task4 `persistent_a_field@77`: FALSE

## Real-source provenance
The source rows are pinned to retained Git objects:
- #1639 formal summary `8557cc1a70487df7abbfffb965a9e4d38ac3bfd5`;
- Chromium persistent runtime events `78cfc40ce061f89c870ec1afc2bc724c391bd4cd`;
- guarded-macro fixture/report `349b4e19d88d718f159dabc362136f5a02b1ed89` / `ee13e4abe3f77f2234bc69e1a948170a979523c5`.

The retained Chromium raw trace provides an exact current target transition on the same persistent handle:
- task3: observation sequence58, status VALID, eligible true, patch `3f7a4324...`;
- task4: observation sequence77, status MISSING, eligible false.
The adapter preserves the observation sequence in the commit-bound lineage.

## Negative controls
All fail closed:
- coarse focus/surface/geometry as target-validity source -> `REJECT_SOURCE`;
- target check relabeled as reusable dependency -> `REJECT_ROLE`;
- unknown source -> `REJECT_SOURCE`;
- unknown target status -> `REJECT_STATUS`;
- wrong pinned source blob -> `REJECT_PROVENANCE`.

This is the concrete enforcement of #1823: source shape/name is not enough. Scope, evidence-backed source admission, role and provenance are all part of adaptation.

## Relationship to the mediated ledger
- Focus-generation currentness may enter the persistent dependency store for its retained scope and later be version/currentness-validated.
- Target-handle currentness is a fresh commit gate only. It may be logged/audited after use, but cannot enter the reusable dependency store.
- #1835 still requires both layers when a consequential action depends on both prepared state and a fresh target/effect gate.

## Integrity
Frozen source identities matched before the one formal invocation:
- fixture `e6ec17a0f49a17153f0f5afde3c9f5f7a75390d3`
- formal `4ed13b11db6121106c7e7cfcefd4fcafcb860c7c`
- audit `2901ee690beff4c7c89deb4a2ab235fdbb1ae4b8`

Formal invocation1; reruns0; replacements0; tuning0.

## Limits
The registry is hand-configured from retained evidence. It does not automatically infer new source applicability, run a new GUI session, measure latency/token benefit, or define a production wire ABI.

## Roadmap disposition
This closes the first retained-real-source adapter implementation slice under #1713:
1. evidence-complete source admission (#1823);
2. two-tier prepare/commit semantics (#1835);
3. lifetime-aware ledger storage (#1848);
4. concrete role adapters for retained focus-generation and target-handle schemas (#1858).

The next phase is shared-caller integration and live coverage measurement, which should start under a separately frozen runtime-integration roadmap because it may touch shared code and active concurrent branches.
