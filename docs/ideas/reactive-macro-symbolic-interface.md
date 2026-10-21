# Reactive motor primitives and compiled symbolic GUI interfaces

**Status at 2026-10-19:** #6 is an open broad research menu; #56 is an open,
focused symbolic-interface hypothesis with retained construction results. They
overlap in local continuation but are not duplicates. This record connects the
idea to its evidence and next audit; it does not close either Issue or authorize
another formal run.

## Distinct questions

- [Issue #6](https://github.com/Unjuno/agent-interface/issues/6) asks whether a
  capable planner can delegate bounded sensorimotor primitives and reactive
  continuation to a local runtime while semantic intent remains with the model.
  Its body is a menu spanning pointer motion, tracking, servoing, macros and
  background execution, not one acceptance test. Its latest comment (2026-09-19)
  audits one-shot backend cleanup in `runtime/cli_v1`; that source repair does
  not test a reactive macro or continuous task.
- [Issue #56](https://github.com/Unjuno/agent-interface/issues/56) narrows a
  different residual: after acquiring an unfamiliar GUI, can the model author
  a bounded symbolic interface of targets, states, actions, effects and
  invalidation rules that supports warm reuse and repair more efficiently than
  repeating screenshots, receipts and coordinates? This is not merely a local
  macro or a rename of existing target handles.

## Retained evidence and limits

- The #56 [A05 48-task reconciliation](https://github.com/Unjuno/agent-interface/issues/56#issuecomment-5976058094) reports A/B/D at 12/12 each and C at 9/12; C used
  a fixed method enum while human code supplied graph semantics and field crops.
  The C arm failed its full correctness gate, so this does not establish a
  planner-authored symbolic interface or an efficiency advantage.
- The separately registered [#7422](https://github.com/Unjuno/agent-interface/issues/7422) R02 contract supplied symbols, states,
  actions, conditions, effects and a crop. Its reported exactness was 10/12 and
  graph success 9/12, so the full disposition was REJECT. The R01 STOP remains
  unchanged. The [result record](https://github.com/Unjuno/agent-interface/issues/56#issuecomment-5976359531) is retained under merged
  [PR #7438](https://github.com/Unjuno/agent-interface/pull/7438); no product
  adoption follows.
- A12–A14 in merged [PR #7353](https://github.com/Unjuno/agent-interface/pull/7353)
  are contract/prompt construction checks. A14's five answers passed the saved
  schema/lifecycle validator ([A14 record](https://github.com/Unjuno/agent-interface/issues/56#issuecomment-5977732499)), but visual review found a blank task-3 screenshot
  elicited task-2-like coordinates. No GUI action, independent application
  effect or 5/5 grounding was measured; the recorded 68,930 input tokens and
  2,688 output tokens are not complete task economics.
- Merged [PR #7616](https://github.com/Unjuno/agent-interface/pull/7616) retains a
  separate offline compiled-graph/pixel-handle composition package. Its own description reports
  `FAIL_SOURCE_BASE_LABEL_MISMATCH`: the candidate labels source
  `41df296...` while `FREEZE.json` pins `9dc383a...`; it also says candidate exit
  code and exact timestamps were not retained. The package is test-double
  composition, not live GUI, application effect or efficiency evidence. A
  read-only audit reproduced the recorded failure without rerunning the
  consumed candidate. Four relevant runtime module blobs match both cited
  source commits, but that does not repair the frozen label mismatch or restore
  the missing candidate exit code/timestamps. The package byte manifests were
  verified after preserving their original line endings. Passing
  navigation/replay checks do not resolve the provenance failure.

## Next finite work

The #7616 audit is complete and retained as a provenance failure; the candidate
was not rerun. This separate #57 offline composition result is not evidence
that #6 or #56 passed their distinct adoption hypotheses. In parallel, the
#6/#56 parent questions remain open. A future
adoption test must compare a planner-authored interface with the strongest
simple existing route over matched cold acquisition, warm reuse and
invalidation/repair tasks, correct application effects, all attempts, actual
calls/tokens, latency and resources; a second domain is required for transfer.
Do not create another abstraction if existing compiled graphs, handles and
guarded callers close the residual.
