# Integrated repair / matched reacquisition accounting v1 — retained first outcome

Decision: **`PASS_REPAIR_REACQUISITION_ACCOUNTING_SCOPED`**.

Primary comparator is frozen: persistent task4/layout-B `repair` divided by ephemeral task4/layout-B `cold` reacquisition. These are different arms, so this is descriptive accounting, not a causal same-arm ablation.

| Unit | Repair | Matched cold reacquisition | Difference | Repair / reacquisition |
|---|---:|---:|---:|---:|
| Wall time | 12.341465157 s | 12.556640965 s | -0.215175808 s | 0.982863585205647 |
| Input tokens | 9,299 | 9,302 | -3 | 0.999677488712105 |
| Output tokens | 161 | 186 | -25 | 0.865591397849462 |
| Reasoning output tokens | 46 | 71 | -25 | 0.647887323943662 |
| Planner generations | 1 | 1 | 0 | 1.000000000000000 |
| Model-visible images | 1 | 1 | 0 | 1.000000000000000 |
| Local observations | 22 | 21 | +1 | 1.047619047619048 |
| Durable calls | 18 | 16 | +2 | 1.125000000000000 |

The immediate repair episode therefore used almost the same wall time and input-token/model-boundary budget as matched cold reacquisition, while using fewer output/reasoning tokens and slightly more local deterministic work. The retained economic benefit should not be described as a large immediate repair discount.

After repair, persistent `repeat_B` (tasks5–6 schedule phase) retains **0 input/output/reasoning tokens, 0 planner generations, and 0 model-visible images**, while using 46 local observations and 40 durable calls. In this allocation, the stronger economic mechanism is restored future reuse after repair, not making repair itself free.

Secondary context is retained but is not substituted into the denominator: plain task4 cold is 9.127145957 s; persistent task1 cold is 11.024952714 s.

Formal invocation: 1; reruns: 0. Independent audit PASS 9/9; five corruption controls all rejected. No synthetic cross-unit scalar is reported.

Scope: one retained Chromium allocation and one layout change only. No population/general speed, monetary cost, second-domain, human-tempo or same-arm causal repair-cost claim follows.
