# #57 post-comparison integration decision

Status: **HOLD for the general integrated-efficiency claim.** The two completed, separately seeded Chromium comparisons reject their respective compiled candidates on correctness/effect gates. The retained-target B arm is a promising matched alternative to fresh-grounding A in both two-block comparisons, but no executed arm combines B's retained-target strategy with the model-authored compiled graph. There is therefore no measured combined-bundle gain or interaction, no basis to promote the full symbolic bundle, and no justification for another same-question crop/predicate tuning run.

This decision joins the published #7413/A05 fixed crop-OCR comparison and #7438/#7422 r02 model-authored contract comparison. Their own source freezes, seeds, task rows, attempts, and scores remain separate. The all-attempt accounting is in the [A05 reconciliation](../compiled_comparison_57_4d74_20261004/a05/accounting-reconciliation/README.md) and [r02 reconciliation](../planner_contract_56_4d74_20261004/r02/accounting-reconciliation/README.md), proposed in PR #7444.

## Composition and arm ownership

| Path | Responsibility in these comparisons | Evidence and disposition |
|---|---|---|
| A: fresh grounding | Re-ground each task from current visual evidence; matched baseline for model-driven paths | 12/12 exact in both comparisons. |
| B: checked retained target | Reuse a revalidated target and invoke model repair/reacquisition only when required | 12/12 exact in both comparisons; descriptive lower token use and task-plus-preflight wait than A in both. Retain as the strongest measured candidate path, without promotion beyond this fixture. |
| C-A05: fixed graph with exact crop OCR | Bounded compiled route using human-fixed template/crops and OCR | 9/12 exact; REJECT this fixed candidate. No general compiled-interface rejection. |
| C-r02: model-authored bounded contract | Model-authored states/actions/conditions/effects consumed by a bounded compiler/runtime | 10/12 exact independent submissions but 9/12 graph successes; REJECT this candidate on full correctness/effect gates. Preserve the exact submission followed by a declared graph effect failure as two distinct observations. |
| D: known-form keyboard route | Human-known form/autofocus behavior and deterministic keyboard input | 12/12 exact in both comparisons and no model calls; setup cost is unavailable, so this is not an end-to-end economic winner. |

The first composed implementation should keep the existing checked-target/revalidation, effect verification, and typed safe-yield boundaries. A planner-authored contract may remain an optional, bounded candidate behind those boundaries, but the current evidence does not authorize selecting its branch or effects as a replacement for them. The studies did not run a B-plus-C arm, so this is a proposed responsibility split for a future owner-approved transfer test, not an implemented or measured bundle.

## Reconciled measurements

Each table cell is a per-planned-task value across two six-task blocks. “Tokens” is input plus output from every task attempt and both arm/block schema preflights. Cached input and reasoning output are subsets and are not added. “Wait” is task elapsed plus separate schema-preflight wait; task elapsed already contains task model wait. Both exclude process startup and final independent scoring.

| Comparison | Arm | Exact independent effects | Graph successes where reported | Model attempts | Input+output tokens/task | Task+preflight wait/task |
|---|---|---:|---:|---:|---:|---:|
| A05 | A | 12/12 | — | 14 | 15,635.50 | 10.5087 s |
| A05 | B | 12/12 | — | 6 | 6,572.83 | 9.3580 s |
| A05 | C fixed crop-OCR | 9/12 | — | 6 | 6,590.17 | 11.8882 s |
| A05 | D known form | 12/12 | — | 0 | 0 | 2.4803 s |
| r02 | A | 12/12 | — | 14 | 15,653.92 | 11.3621 s |
| r02 | B | 12/12 | — | 6 | 6,584.83 | 9.4121 s |
| r02 | C model-authored | 10/12 | 9/12 | 9 | 10,620.75 | 17.4722 s |
| r02 | D known form | 12/12 | — | 0 | 0 | 1.8090 s |

B versus A reduces input-plus-output by 57.96% and task-plus-preflight wait by 10.95% in A05; r02 gives 57.93% and 17.16%, respectively. These are descriptive point estimates from two blocks, not a population or causal generalization. A05 C costs 0.26% more input-plus-output and takes 27.04% longer than B while failing three exact tasks. r02 C costs 61.29% more input-plus-output and takes 85.64% longer than B; it reaches 10/12 exact submissions but only 9/12 graph successes. Both C candidates fail the correctness/effect gate, so neither qualifies for a benefit claim.

## Requirement and residual map

- **Finite matched comparison and retained failures:** satisfied for these two fixed Chromium allocations. r02 preserves its earlier image-free preflight STOP separately; it is not counted as an r02 formal task block or pooled into r02's 29-attempt comparison.
- **Cold, warm, reacquisition/repair phases:** observed in the bounded candidate paths. The model-authored r02 planned task-4 OCR repairs fail in both blocks; later layout-B reacquisition/reuse successes do not erase those failures.
- **All-attempt actual model-token accounting:** reconciled independently for A05 (26 attempts) and r02 (29 attempts). Monetary cost is UNKNOWN; human setup cost is UNAVAILABLE.
- **Task effects and collateral submissions:** the archived independent scorers report no duplicate or unexpected submissions. This does not establish arbitrary collateral-content safety, complete authority proof, or privacy/redaction composition.
- **Planner-authored contract execution:** r02's post-run custody audit joins provider-authored contracts through compiled graph/branch/transition/native terminal for all 12 C rows. Its observed effect failure and task failures remain dispositive for this candidate.
- **Measured combined bundle/interaction:** missing. Neither study runs a predeclared arm that combines B with C; do not add the separate B gains or infer synergy.
- **Transfer and product claims:** a second domain, current-main product qualification, complete acquisition/setup economics, and human-tempo performance remain unverified.

## Decision boundary

REJECT the two measured C candidates as configured. RETAIN B only as a descriptive, fully correct candidate for this fixed fixture. HOLD the broader #56/#57 integrated-efficiency claim until an owner selects a genuinely unresolved transfer or composition question, declares a finite comparison including the actually combined arm and all cold/warm/invalidation/repair costs, and closes the applicable authority, effect, collateral, and privacy gates. Do not retune the rejected fixed crop or predicate under the same question, and do not claim saturation from this small block.

No formal allocation, provider call, GUI action, or new experiment was performed to write this synthesis. The reconciliations prove internal arithmetic over retained JSON only; their own provenance and audit limitations still apply.
