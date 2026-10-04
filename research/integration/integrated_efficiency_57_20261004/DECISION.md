# #57 post-comparison integration decision

Status: **HOLD for the general integrated-efficiency claim.** The two completed, separately seeded Chromium comparisons measured retained-target reuse/reacquisition with compiled continuation: A05 used a fixed compiled route, and r02 used a model-authored bounded graph. Both C candidates failed their full correctness/effect gates. These results establish neither a beneficial qualified general bundle nor the causal interaction of the graph with retained-target reuse; they do not leave that composition wholly unmeasured. There is no basis to promote the full symbolic bundle, and no justification for another same-question crop/predicate tuning run.

This decision joins the published #7413/A05 fixed crop-OCR comparison and #7438/#7422 r02 model-authored contract comparison. Their own source freezes, seeds, task rows, attempts, and scores remain separate. The all-attempt accounting is in the [A05 reconciliation](../compiled_comparison_57_4d74_20261004/a05/accounting-reconciliation/README.md) and [r02 reconciliation](../planner_contract_56_4d74_20261004/r02/accounting-reconciliation/README.md), proposed in PR #7444.

## Composition and arm ownership

| Path | Responsibility in these comparisons | Evidence and disposition |
|---|---|---|
| A: fresh grounding | Re-ground each task from current visual evidence; matched baseline for model-driven paths | 12/12 exact in both comparisons. |
| B: checked retained target | Reuse a revalidated target and invoke model repair/reacquisition only when required | 12/12 exact in both comparisons; descriptive lower token use and task-plus-preflight wait than A in both. Retain as the strongest measured candidate path, without promotion beyond this fixture. |
| C-A05: fixed graph with exact crop OCR | Bounded compiled route using human-fixed template/crops and OCR | 9/12 exact; REJECT this fixed candidate. No general compiled-interface rejection. |
| C-r02: model-authored bounded contract | Model-authored states/actions/conditions/effects consumed by a bounded compiler/runtime | 10/12 exact independent submissions but 9/12 graph successes; REJECT this candidate on full correctness/effect gates. Preserve the exact submission followed by a declared graph effect failure as two distinct observations. |
| D: known-form keyboard route | Human-known form/autofocus behavior and deterministic keyboard input | 12/12 exact in both comparisons and no model calls; setup cost is unavailable, so this is not an end-to-end economic winner. |

The first composed implementation should keep the existing checked-target/revalidation, effect verification, and typed safe-yield boundaries. A planner-authored contract may remain an optional, bounded candidate behind those boundaries, but the current evidence does not authorize selecting its branch or effects as a replacement for them. The measured C paths already include retained-target behavior, so a new arm label or a B-plus-C name alone does not justify repeating them. Any future owner-approved transfer test must target a genuinely unresolved question and predeclare the needed causal contrast.

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

The open PR #7353's earlier requirement map is useful source material, but its pre-A05 disposition is stale. This table reapplies those requirements to the merged A05 and r02 results; it does not modify or adopt the unmerged PR branch.

| Requirement | Current evidence | Disposition after A05/r02 |
|---|---|---|
| #52 no-match, ambiguity, unavailable/exhausted; typed distinction among stop/failure/incomplete | Live tasks exercised correct routes and typed OCR/effect safe-yields. No adversarial ambiguity, unavailable-evidence or exhaustion task was included in either six-task formal block. | Partial: successful/effect-failure/stop behavior is observed; required negative branches remain test-double/component evidence, not full live composition. |
| #53 all-attempt accounting, failed calls, repair, missing usage | Separate joins reconcile A05's 26 and r02's 29 calls, including six schema preflights each and all published usage fields. Task4 model-authored repairs fail in both r02 blocks. | Partial: actual provider counters and all recorded calls reconcile; this does not cover a missing-usage `null` call joined through a live repair path. Preserve r02 r01 STOP as its own 11-attempt outcome. |
| #54 schema preflight before GUI authority and separate preflight charge | Each comparison retains six arm/block preflights; reconciliations assign those six calls and waits to A/B/C, with D at zero. | Pass for observed preflight order and accounting in these runs; no claim beyond the frozen caller/fixture. |
| #55 identity after model wait; freshness is not identity | B/C runs include target revalidation and the changed-layout reacquisition path. Independent scorer and runtime evidence retain outcomes. | Partial: correct fixture effects are observed, but neither block injects an adversarial identity change during model wait and then independently tests stale-target admission. |
| Scope, focus/surface, lease, cancellation, release, bounded progress, uncertain delivery, no blind replay | Native execution/release records and exact terminal effects are retained for the exercised tasks; failures stop without blind retry. | Partial: normal-path release and bounded safe-yield are observed. Deliberate focus/surface, lease, cancellation and uncertain-delivery fault injection are not part of these formal comparisons. |
| Independent effect, collateral, completed prefix, evidence identity/retrieval, privacy | Both independent scorers report no duplicate or unexpected submissions. r02 post-run custody audit joins provider contracts through graph/branch/transition/native terminal for 12 C rows. A05/r02 audits are post-run and bounded in scope. | Partial: task effects and scoped custody are checked; arbitrary collateral-content safety, complete authority proof, privacy/redaction and full caller receipt/raw-retrieval composition remain open. |
| #12/#46 matched comparison integrity and benefit eligibility | Same six-task fixture within each two-block comparison, counterbalanced arm order and all attempts retained; all report rows are reconciled separately. | Pass for these finite descriptive comparisons. Two blocks do not establish population reliability or uncertainty bounds; failing C arms are ineligible for benefit claims. |
| Cold, warm, invalidation/reacquisition, repair | Cold and warm use plus changed-layout reacquisition are represented. r02 C has later reacquisition/reuse successes, but both planned task4 OCR repairs fail. | Partial: phase execution is observed; required repair success is not established for the model-authored candidate. Failures remain in the denominator. |
| Measured combined bundle/interaction | A05 C measured retained-target reuse/reacquisition with fixed compiled continuation; r02 C measured retained-target reuse/reacquisition with a model-authored bounded graph. Both C candidates failed their correctness/effect gates; C also changes other factors, so the graph's causal interaction is not isolated. | Partial: these are executed compositions, but neither qualifies as a beneficial general integrated bundle or isolates graph interaction. Do not add B's separate improvements or infer synergy. |
| Transfer/product/economics | Both are pinned Chromium research fixtures. Money and human setup cost are unavailable. | Missing: second-domain transfer, current-main product qualification, complete setup/acquisition economics and human-tempo performance remain unverified. |

The finite matched-comparison and attempt-retention gates are satisfied for these two fixed allocations. r02's earlier image-free preflight STOP remains separate; it is neither erased nor counted as a task block in the 29-attempt r02 comparison. Monetary cost is UNKNOWN and human setup cost is UNAVAILABLE.

## Decision boundary

REJECT the two measured C candidates as configured. RETAIN B only as a descriptive, fully correct candidate for this fixed fixture. HOLD the broader #56/#57 integrated-efficiency claim until an owner selects a genuinely unresolved transfer or composition question, declares a finite comparison including the actually combined arm and all cold/warm/invalidation/repair costs, and closes the applicable authority, effect, collateral, and privacy gates. Do not retune the rejected fixed crop or predicate under the same question, and do not claim saturation from this small block.

No formal allocation, provider call, GUI action, or new experiment was performed to write this synthesis. The reconciliations prove internal arithmetic over retained JSON only; their own provenance and audit limitations still apply.
