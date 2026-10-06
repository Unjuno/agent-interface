# A15 — transition-state abstention construction check

## Question

Can a model-authored bounded interface distinguish a retained pre-navigation screenshot with no current form controls from the immediately following screenshot where the same task form is visibly ready, using an explicit abstention-capable output schema?

## Frozen inputs and conditions

Two exact retained screenshots for task 3 are used in fixed order: `transition_053.png` (sequence 053; browser navigation is in progress and the prior SAVED page remains visible, with no Value field or Save button) and `ready_054.png` (sequence 054; task-3 page with visible editable Value field and Save button). SHA-256 values, original main paths, current-main source commit, model, CLI version, prompt/schema/compiler identities, and commands are pinned in `manifest.json`. Before the model calls, the images were visually inspected at native 1280x800 resolution.

Exactly one independent model-only CLI call per screenshot is allowed, in the listed order, using gpt-5.6-luna at low effort and the same prompt and output schema. Per-call timeout is 90 seconds. No retries. If one call fails or is incomplete, preserve it and continue to the other pre-frozen case. No application, GUI input, live observer, or formal allocation runs.

The output schema allows either READY with coordinates/crop/contract, or ABSTAIN with all target-bearing fields null. The positive contract is checked with the pinned A12 predicate-lifecycle guard and R02 compiler.

## H/T/D/C/U

- **H:** The model abstains on sequence 053, producing no coordinates, crop, or contract, and produces a correctly grounded, A12-compilable READY contract on sequence 054.
- **T:** One same-model, same-prompt, same-schema call per pinned image. Independently audit status/null fields, positive point/crop geometry against pre-reviewed target regions, output shape, and A12 compiler/lifecycle acceptance.
- **D:** PASS only if the transition frame is ABSTAIN with reason targets_not_visible and all target-bearing fields null, while the ready frame is READY with reason none, correct in-bounds points/crop, and an A12-accepted contract preserving per-action target_valid guards and exact token/save effects. Any false READY on 053, abstention on 054, malformed geometry, compiler refusal, timeout, missing output, or unaccounted attempt fails or leaves the batch incomplete as specified in the raw results.
- **C:** Two fixed adjacent frames from one synthetic Chromium form fixture; one sample per frame and one model version. This does not measure stochastic reliability, new-coordinate generalization, different-app transfer, or execution correctness. The A14 task-3 review label is contradicted by the exact pinned PNG: sequence 054 contains the form; sequence 053 is the appropriate retained no-control transition frame.
- **U:** Prompt/schema construction only. No target admission, GUI action, release, application effect, safety/collateral qualification, cross-domain transfer, or efficiency claim.

No historical A05 or R02 score is changed. This construction check cannot authorize a formal allocation or runtime adoption.
