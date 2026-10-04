# A14 — five-task lifecycle prompt construction check

## Question and fixed source

Does the A13 predicate-lifecycle prompt clause produce A12-acceptable bounded contracts across the other five retained block-2/C screenshots, beyond its first sampled task? This is a new model-only construction batch over already retained synthetic fixture images; it is not a replay, GUI allocation, or attempt to revise the R02 result.

The five inputs are tasks 2–6, each paired with its original R02 C-arm task row, runtime screenshot, alias map, token, and captured `gpt-5.6-luna` / low setting. Screenshots are all 1280×800. The original task rows and image bytes are pinned in `manifest.json`. Each task gets exactly one independent Codex CLI invocation with the A13 prompt template and the exact same copied schema. Per-call timeout is 90 seconds; no retries. Continue other pinned tasks if an individual call fails, preserving each first result. No GUI tools or external application connections are enabled; CLI sandbox is read-only.

## H/T/D/C/U

- **H:** All five single-call outputs satisfy the saved schema, retain `target_valid=true` on both action branches, omit it from both action effects, require `exact_token_visible=true` after entry, and require `exact_saved_title=true` after Submit and at completion; the A12 candidate wrapper accepts all five.
- **T:** For each frozen task 2–6 input, invoke the same model and low effort once with that task's retained token, screenshot, and pinned output schema. Audit each returned object for the listed requirements, bounded points/crop, and A12 compilation using that row's aliases.
- **D:** PASS only if all five calls exit zero without timeout and all five independent row audits pass. Any incomplete or nonconforming row fails the batch gate and remains retained. No retry or threshold adjustment.
- **C:** One model sample per task, same synthetic form family, same model/effort, images already represented in R02, and no live GUI/scorer. The samples are not statistically independent generalization evidence.
- **U:** Visual grounding correctness, exact entry/save effect, cancellation/release, environmental transfer, robustness beyond these five samples, end-to-end cost, and integrated efficiency remain unmeasured.

No task score is changed or inferred. R02 remains immutable. This batch cannot authorize a formal allocation or product adoption.
