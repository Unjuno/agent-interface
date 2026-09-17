# Integrated post-repair reuse payback v1 — retained first outcome

Decision: **`PASS_POST_REPAIR_REUSE_PAYBACK_RECONSTRUCTED_SCOPED`**.

Primary horizon is frozen to the retained task4–task6 schedule only:

- persistent: `layout_change` repair + `repeat_B` reuse;
- ephemeral: `layout_change` cold + `repeat_B` cold/nonpersistent work.

No preflight, acquisition, repeat_A, synthetic future tasks, or cross-unit scalar enters the comparison.

| Unit | Persistent task4–6 | Ephemeral task4–6 | Persistent − ephemeral | Persistent / ephemeral |
|---|---:|---:|---:|---:|
| Wall time | 24.874512215 s | 37.921563313 s | -13.047051098 s | 0.655946380946608 |
| Input tokens | 9,299 | 27,906 | -18,607 | 0.333225829570702 |
| Output tokens | 161 | 567 | -406 | 0.283950617283951 |
| Reasoning output tokens | 46 | 222 | -176 | 0.207207207207207 |
| Planner generations | 1 | 3 | -2 | 0.333333333333333 |
| Model-visible images | 1 | 3 | -2 | 0.333333333333333 |
| Local observations | 68 | 65 | +3 | 1.046153846153846 |
| Durable calls | 58 | 48 | +10 | 1.208333333333333 |

The retained task4 repair episode alone had only a 0.215175808 s wall advantage over matched ephemeral task4 cold and nearly identical input-token cost (#947 context). Across the actually observed post-repair horizon, however, tasks5–6 require **zero** persistent model input/output/reasoning tokens, zero planner generations, and zero model-visible images. The cumulative task4–6 wall margin grows to **13.047051098 s**.

Thus the retained economic mechanism is sharper than “repair is cheap”: repair restores a reusable local interface, and the subsequent observed reuses remove two additional model boundaries/images and 18,604 input tokens in this allocation. This occurs with slightly higher local deterministic work, which remains a separate unit and is not converted into model-equivalent cost.

Formal invocation: 1; reruns: 0. Independent audit PASS 11/11. Five corruption controls rejected 5/5.

Scope: one retained Chromium allocation, one layout change, exactly two observed post-repair reuse tasks. Different-arm descriptive accounting only; no same-arm causal ablation, population/general speed, monetary cost, human-tempo, second-domain, or extrapolation beyond task6.
