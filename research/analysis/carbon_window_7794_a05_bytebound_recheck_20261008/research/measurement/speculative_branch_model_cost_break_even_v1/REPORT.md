# Break-even budget for second-branch model authoring — first outcome

Decision: `PASS_MODEL_BRANCH_AUTHORING_BREAK_EVEN_LOCALIZED_SCOPED`.

This analysis does **not** estimate actual model branch-authoring cost. It localizes the maximum incremental same-generation model wall that the second speculative branch may consume before the previously retained K2 temporal configuration loses its scoped synthetic latency advantage over K1.

Exact retained parent values:

- K2 temporal mean realized-to-effect latency: **5.8027 ms** (#1127);
- K1 temporal mean: **13.62925 ms** (#1153);
- raw K2 advantage: **7.82655 ms**;
- #1174 local second-branch marginal preparation cost: mean **0.05901920322 ms**, p50 **0.052169 ms**, p95 **0.104828 ms**, p99 **0.219330 ms**.

Residual model-side break-even budgets:

- after mean local cost: **7.76753079678 ms**;
- after p50 local cost: **7.774381 ms**;
- after p95 local cost: **7.721722 ms**;
- after p99 local cost: **7.607220 ms**.

The conservative future matched-model discriminator should use the **p95 budget = 7.721722 ms**: if the measured incremental wall for authoring branch 2 inside the same generation is below this budget, K2 remains latency-favored under this frozen synthetic comparison; above it K1 becomes latency-favored after charged local + model cost; equality is break-even/HOLD.

A retained model-boundary probe has a 4.9053379 s local agent-message-arrival reference. It is deliberately typed as an **extra/full boundary reference only**, not as same-generation incremental branch cost. The probe used a different task/context and did not expose served-model identity. Substituting that seconds-scale value into the same-generation cost slot would be semantic laundering.

The legitimate next model experiment is therefore tightly specified: one fixed model/settings, identical prompt/evidence/schema except K1 vs K2 branch allowance, both branches authored in the **same generation**, paired provider usage plus local output-arrival timing, and no extra model boundary. Actual model cost remains `UNMEASURED` here.

Independent audit PASS; frozen copied-result corruptions5/5 reject; source rehash exact; formal invocation1/reruns0; model/provider/GUI/task-input actions0.
