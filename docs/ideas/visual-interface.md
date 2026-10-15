# Visual representation, addressing and feedback ideas

Consolidated 2026-10-15 from #3, #5 and #8. **Disposition: retained ideas, not currently scheduled.** Closing their intake Issues does not assert scientific completion, rejection, or successful deployment. Original Issue bodies and metadata are retained in [the source snapshot](visual-interface-sources-20261015.json); the live Issues remain the discussion provenance.

## Optional grids — #3

Source: [Explore model-selectable visual grids for agent-centric pointing](https://github.com/Unjuno/agent-interface/issues/3).

Hypothesis: a deterministic grid or region address may improve fine pointing and reduce corrective observations. Compare no grid, always-on grid, model-selectable grid and coarse-to-fine/ROI grid on matched fresh tasks. Preserve the original observation, coordinate mapping and presentation provenance. A grid may obscure controls or increase image/token cost; it must not compensate for unresolved pointer/application-effect semantics.

Revisit when a concrete targeting failure justifies this intervention. Specify task-effect correctness, endpoint error, corrective actions, latency and measured model cost before testing. This consolidation does not review or establish the outcome of every later grid-related study.

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

## Intake closure and later work

At review time all three Issues were open, had no comments and had no closing references among the 538 open PRs retrieved. This is evidence about those discussions and formal PR references, not proof that there is no related implementation or informal worker assignment. No live resource or allocation is transferred by closing these idea menus.

Future work should reopen the relevant source Issue or use a focused task linking the relevant section, its current-code residual, a finite experiment and a decision rule. Unscheduled ideas remain discoverable here without all being open tasks.
