# Intent-bounded Needle distillation pilot 01

Issue: [#3458](https://github.com/Unjuno/agent-interface/issues/3458)

## H / T / D / C / U

- **H:** A compact learned head can imitate a fixed bounded decision teacher at >=0.95 held-out accuracy, <=1% false CORRECT proposals, <=10 KiB state, and <60 ms CPU p95 while an independent stale/intent/scope/state gate yields.
- **T:** Frozen runner SHA-256 `2542160E16D7C5BEC2C67598DC07182847A473644A5C61A87427A92D5E406330`; seed 3458; 8,192 train / 4,096 random test states; 6→16→16→3 MLP; 700 AdamW steps. Host CPU inference because Docker Desktop Linux engine was unavailable.
- **D:** Scalar preregistered numeric gates pass (accuracy .98584, false CORRECT 33/4096=.806%, model state 4,040 B, CPU p95 .1139 ms); however CONTINUE had only one test example and it was wrong. Overall disposition **HOLD_TEST_CLASS_COVERAGE**, not a general Needle pass.
- **C:** Same fixed teacher and data schema for exact rule baseline and learned student; external deterministic gate is independent of the student.
- **U:** Teacher is synthetic and hand-authored, one random seed; no Astra labels, live observation, GUI/action, or end-to-end servo. Rule p95 .0579 ms vs student .1139 ms; no latency advantage demonstrated.

Invalid metadata/state probes all YIELD: stale epoch, wrong intent, wrong scope, out-of-envelope state, nonfinite state. Exact metadata allows only a local proposal, never execution authority.

Next: stratify a fresh successor test across all output classes and near decision boundaries; preregister per-class recall, false-action rate, and rule-vs-student latency before one execution. Preserve this HOLD result unchanged.

Files: [runner.py](runner.py), [RESULT.json](RESULT.json).