# Target review with one optional screen image

## Integration decision

Add optional `screen_region=[x,y,width,height]` to persistent public MCP `interface_inspect_target`. The existing read-only observation/presentation path returns one image with focused-client evidence. Metadata is checked before/after capture. Capture failure or disagreement returns no review ID; explicit target selection and its fresh recheck remain separate. The 30-second review deadline is unchanged and starts after inspection work. No focus, input, recovery reset, automatic retry, sensor or helper model is introduced.

Adopt only this optional composition and the observed input guidance. **HOLD_GENERAL_BATCH_EFFICIENCY_CLAIM**: fewer requests did not guarantee correct Save-As. Neither the screenshot nor equal metadata is a widget-processing or redraw acknowledgement.

## Three retained primary-operated Inkscape trials

All use private Xvfb/Openbox, public persistent MCP over the SDK, the same seed 991305, the same starting SVG, Right x3, and Save As `saved-copy.svg`. Initial SVG x50/y50/w40/h30 must remain unchanged; requested copy must have x56/y50/w40/h30. No helper model or subagent chose actions. The order is fixed, first baseline then candidate then an adapted interaction policy. The candidate comparison was specified after observing baseline; this is exploratory, not a preregistered randomized or replicated experiment.

| Trial | Live source | Public calls | Input dispatches | Images | Independent result |
| --- | --- | ---: | ---: | ---: | --- |
| 01 separate inspection/capture | ab10e238c | 11 | 2 | 6 | Correct saved copy; one expired review refused |
| 02 combined inspection/image | a149335fc | 8 | 2 | 6 | Wrong filename `shape.svgsaved-copy.svg`; requested copy absent |
| 03 combined, reviewed field stages | a149335fc | 10 | 4 | 8 | Correct saved copy after selection/value review |

Trial 01's initial dispatch returned the old main surface before the file dialog painted. Metadata inspection saw the dialog; a fresh screen was then viewed, but its review request exceeded the recorded deadline. That refusal sent no input and is retained. A new explicit inspection/review succeeded. Batched click/Ctrl+A/text/Save happened to save correctly.

Trial 02 delivered the actual dialog image and metadata together and selected it without a review refusal. The same input program later saved the wrong filename. The primary viewed both the concatenated filename in the dialog and the wrong document title, declared failure and stopped. The wrong-name SVG was copied after input/close for independent evidence, not used to select a retry. The expected output was absent and the task evaluator returned false. Both input dispatches still reported completed with verified release: input completion is not task correctness. This single observation does not isolate the cause of the missing replacement or attribute it to bundled observation.

Trial 03 changed the action policy, not runtime code: the primary first viewed full `shape.svg` selection, then viewed exact `saved-copy.svg` after typing, then chose Save. A fresh final capture showed the correct document title and geometry; independent SVG parsing confirmed the copy and unchanged original. It added two input/observation stages. This is one follow-up success, not proof that the policy generally prevents wrong saves or improves speed.

All trials retain requests/responses, images, source freezes, SDK timing, original/output files, review refusals and cleanup. Each used one session, closed with verified empty input state and ended client/fixture exit 0. Fixture close returned; no independent all-descendant process claim. Each primary-review.json lists images actually viewed. Absolute tmp paths differ by fresh fixture.

## Measurements and checks

SDK call sums were 1519.05 ms, 1319.25 ms and 2194.46 ms respectively. The lowest sum belongs to a failed task. The sums exclude primary thinking and orchestration; separate overall client intervals include them but do not isolate model latency. PNG byte counts are not token measurements. Actual model input tokens/cost and host image-ack latency remain unavailable. See comparison.json for exact intervals and counts; no general ranking or human-tempo claim.

The structural composition replaces a separate metadata-inspection plus capture pair with one public call when both are needed. It does not eliminate the explicit target review or subsequent observation. Trial 02's three-call difference includes avoided expiry recovery and is not a clean estimate of that structural saving.

Shared local checks: 195 protocol + 79 harness tests; portable distribution: 7 tests. New focused cases cover combined image delivery/retained reread without recapture, ordinary target changes during capture, and an invalid capture region producing no review ID. General selection/focus/typing timing remains unresolved.

Run `python runtime/results/target-review-image-01/verify.py`. It checks all 292 retained files, decodes delivered image blocks, matches combined image artifact hashes, independently parses SVG outputs and retains failed task outcomes. It does not substitute hashes or fixture checks for a task-performance result. Research #4079 remains a separate cooperative application-value study; this primary GUI observation does not confer its value-receipt guarantees on generic XTEST.