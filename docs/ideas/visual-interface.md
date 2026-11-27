# Visual representation, addressing and feedback ideas

Consolidated 2026-10-15 from #3, #5 and #8, then extended with the distinct adaptive-view question from #7. **Disposition: research to organize and execute.** The current source Issues #4, #5, #7 and #8 are open; #3 is also open after its earlier archival closure was corrected. The broad #4 interface thesis is the north star, while #3 (grid presentation), #5 (address/feedback contracts), #7 (which set of views to present under a budget), and #8 (how to pack selected views) remain distinct questions. Use [the execution agenda](visual-interface-agenda.md) for priorities, dependencies and next experiments. Original bodies and metadata for #3/#5/#8 remain in [the historical source snapshot](visual-interface-sources-20261015.json); read live sources before changing any Issue state.

## North-star relation — #4

Issue [#4](https://github.com/Unjuno/agent-interface/issues/4) asks whether human-designed screenshot/reason/coordinate interfaces limit a capable model, while retaining universal GUI fallback. It is an open design thesis, not an executable feature or acceptance gate. Evaluate each concrete intervention below against correctness, independent task effect and matched cost; a component result cannot complete the broad thesis. The maintained summary is in [Ideas and outcomes](../IDEAS_AND_OUTCOMES.md).

## Optional grids — #3

Source: [Explore model-selectable visual grids for agent-centric pointing](https://github.com/Unjuno/agent-interface/issues/3).

Hypothesis: a deterministic grid or region address may improve fine pointing and reduce corrective observations. Compare no grid, always-on grid, model-selectable grid and coarse-to-fine/ROI grid on matched fresh tasks. Preserve the original observation, coordinate mapping and presentation provenance. A grid may obscure controls or increase image/token cost; it must not compensate for unresolved pointer/application-effect semantics.

Revisit when a concrete targeting failure justifies this intervention. Specify task-effect correctness, endpoint error, corrective actions, latency and measured model cost before testing. This consolidation does not review or establish the outcome of every later grid-related study.

## Adaptive multi-view selection — #7

Source: [Explore adaptive multi-view observation without overloading the planner](https://github.com/Unjuno/agent-interface/issues/7).

Hypothesis: for a fixed task and model-visible cost budget, selecting a complementary set of views (for example, overview plus target and destination) can reduce uncertainty or correction loops enough to justify its extra image/token, comparison, preparation and latency cost. The question is the value of the selected **set**, not whether extra images or bytes are automatically cheaper.

The 2026-10-20 source/report crosswalk is in the [family disposition receipt](../maintenance/issue-family-disposition-visual-multiview-20261020.md). It distinguishes the invalid original #1946 claims in closed-unmerged PRs #1947/#1951 from corrected #1968 successors: merged PR #1981 is a scoped formal/audit pass for exact serialized recovery and duplicate-label controls; merged PR #1983 is a separate 24-row local-only `HOLD_NO_FORMAL_CONTAINER`. Both use fixture-derived regions and neither establishes model utility. Keep #1946 open: #1981's three-case result does not meet the full original fixture gate, and the broader #1983 result lacks the required container-backed formal run and independent audit. The original early PASS is not accepted. #7 remains open for the separate fixed-budget view-set utility hypothesis.

Issue #2031 retains 32 local Gemma 3 calls, but the per-arm `1/8` scores are invalid as pure accuracy because successful selection responses omitted the scorer-required Boolean abstention field. The auditor cap was exceeded after an initial infrastructure STOP, and the preserved bundle has a 113/114 manifest match with the REPORT digest unresolved. The records are diagnostic only: no utility or formal all-gates PASS is demonstrated. The separate merged PR #2173 is only a four-case provenance-construction gate.

Next package-integrity discriminator for #1946: only on a verified eligible new allocation, run the exact full frozen multi-resolution fixture gate under its required container and independent audit; do not reuse a consumed allocation or substitute #1981's narrower result. Next utility discriminator for #7: preregister a held-out, same-model comparison with identical task semantics and a fixed model-visible budget: overview only, best single ROI, duplicate/same-information views, and complementary target+destination views. Measure independently scored task correctness, errors/corrections, actual image/token accounting, planner calls, latency and preparation cost. Do not infer model utility from encoded-byte savings or re-run a consumed package allocation. #2031 remains open for an explicitly corrected successor; #7 remains open for the broader view-set hypothesis.

## Visual addresses and feedback contracts — #5

Source: [Explore agent-native visual addressing and feedback contracts](https://github.com/Unjuno/agent-interface/issues/5).

This is a research menu, not a single executable task. Its eight parts are preserved here: (1) observation/surface/frame-bound visual addresses; (2) selectable presentation; (3) deterministic visual anchors; (4) bounded visual servo; (5) separate latest state and retained events; (6) explicit input/program/effect/task completion levels; (7) continuation tickets bound to the original owner/revision/lease; and (8) self-describing operation schemas.

Keep universal screenshot/keyboard/pointer control available. Historical observation and presentation metadata do not grant authority. Reject stale references; do not extend leases or silently restore released input. Measure application effect separately from cursor motion. Continuation must replace/yield a preplanned tail safely, rather than racing it. Local neural control is not required by this proposal.

Revisit one component at a time when current code or task evidence demonstrates a missing capability. Trace the actual caller and existing implementation before opening a new task; this menu may already overlap implemented components. A matched correctness-preserving comparison, source-bound evidence and scoped adoption decision are required for any new mechanism claim.

## Composite observations — #8

Source: [Explore composite visual packing to reduce multi-view context cost](https://github.com/Unjuno/agent-interface/issues/8).

Hypothesis: packing overview/target/destination/temporal views into a deterministic labeled composite may preserve useful information with less planner effort or context cost. Compare plain overview, separate images, a composite with the same information and a task-relevant composite. Record panel/source rectangles, scale, source observation and inverse coordinate mappings; distinguish current from historical panels.

Costs depend on model/provider image processing. Fewer images or fewer bytes do not prove fewer tokens or less latency. Measure correctness, task time, planner calls, preparation cost, actual image/token accounting, endpoint/effect error and panel-confusion failures on fresh tasks. Preserve plain screenshot fallback; keep this optional if benefits are task-specific.

Revisit when a measured multi-view cost justifies a matched packing experiment. Do not silently add a semantic selector or change information content between comparison arms.

## Execution tracking

2026-10-19 live recheck: #4, #5, #7 and #8 are open; #3 is open after its earlier close/reopen correction. #4 has no comments; #5 retains current guarded-caller evidence and unresolved native/task-effect boundaries; #7 has a budgeted ROI-set research note and an explicit #1946 reuse instruction; #8 was reopened after the maintainer clarified that archiving must lead to organized research. Keep closure history in the source Issues. This summary is navigation, not evidence that a hypothesis passed or that an allocation is available.

Track remaining experiments in the existing Issues. The agenda must distinguish existing component results from untested integration and new experiments. Consolidation is complete only when the distinct hypotheses and their next research actions have been accounted for, not when the intake count falls.
