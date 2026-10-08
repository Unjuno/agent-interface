# Planner-gap temporal speculation Rung1 A2 — first outcome

Decision: `HOLD_NO_LATENCY_DISCRIMINATOR`.

The frozen 400,000-case corpus reproduced the retained Rung0 aggregate branch hit rates exactly: current-only 75.907% vs temporal-informed 83.991%. With the frozen 40 ms planner gap, fresh state at10 ms and1 ms modeled local hit handling, mean realized-state→effect latency was WAIT 31.0000 ms, CURRENT_ONLY 8.2279 ms, TEMPORAL_INFORMED 5.8027 ms. Temporal beat current-only by 2.4252 ms, below the preregistered >=3 ms PASS gate, while beating WAIT by 25.1973 ms. Therefore the scoped result is HOLD, not PASS.

The real subprocess discriminator passed its local gates: all72 arm-runs independently logged EFFECT_APPLIED with wrong0. Median realized→effect latency was temporal 0.8038 ms, current 30.9157 ms and wait 30.8755 ms. These discriminator cases were intentionally selected where temporal hits and current-only misses, so they establish mechanism latency, not population-average benefit.

The useful negative result is quantitative: an +8.084 percentage-point branch-hit gain is insufficient to cross the frozen 3 ms average-benefit gate when only 30 ms of post-realization planner wait is avoidable. Do not lower the threshold or lengthen the gap inside this allocation. A successor should change one scientific factor only if that factor is independently motivated (for example an actually measured planner-gap distribution); otherwise retain the simpler current-only baseline for this scoped 40 ms setting.

Source rehash exact; copied-result corruption controls 5/5 add errors; formal invocation1/reruns0; no model/GUI/X11/OS task input.
