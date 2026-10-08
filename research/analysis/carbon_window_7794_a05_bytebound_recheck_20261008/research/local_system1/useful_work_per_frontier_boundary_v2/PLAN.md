# Useful work per frontier boundary v1

Task: `LOCAL-SYSTEM1-USEFUL-WORK-PER-FRONTIER-BOUNDARY-20260917-001`

Publication base: `817073c8074ba7951dc9f2383a6abff4e104dac3`.

H: The retained persistent Chromium arm yields exactly 3 verified tasks per task-time planner generation, 2 verified tasks per total generation including preflight, and 4/6 verified task-time tasks with zero planner generation, while retaining higher local observation/durable-call counts and task-2 wall break-even.

T: Deterministic standard-library Python over a frozen minimal fixture extracted from exact Git blobs `7db368b2d492b5b95f5f038fb7cb5dd6b78a27a7` (#836) and `d23e2db9ee212d5f7409960301c84a454faf6934` (#922). One formal invocation; reruns/replacements/tuning 0.

D: PASS only if exact task/generation ratios, 4/6 frontier-free persistent task count, local-work increase, retained task6 wall totals and task-2 wall break-even reconcile and independent audit passes.

C: Frontier reductions substitute local observations/durable calls; heterogeneous units are not summed. Six retained tasks do not establish population reliability.

U: One retained Chromium allocation only; no new model/GUI/task input, no active-model-wait concurrency claim, no second-domain or human-tempo claim.
