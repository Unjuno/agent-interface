# #1871 formal stop — ordered interrupt batching

Decision: **STOP_FORMAL_RUNNER_LOCAL_BINDING_BEFORE_RESULT / scientific NONE**.

The first and only formal invocation stopped before any durable scientific row or `FORMAL_RESULT.json`. Python treated `ordered_batch` as a local variable because `run_formal.py` contained a later in-function `from model import ordered_batch`; the first call to `ordered_batch(...)` therefore raised `UnboundLocalError`.

- formal invocations: 1
- reruns/replacements/tuning: 0/0/0
- durable scientific rows: 0
- result file: absent
- stdout: 0 bytes
- wrapper elapsed: 0.61 s
- max RSS: 92,852 KB

The preformal source/readback and 10/10 construction tests remain provenance only; they are not scientific result rows. Do not rerun this task. A legal successor may change exactly one harness factor: remove the local import shadowing while preserving the frozen batch size, corpus, directed controls, decision gates, source semantics, and no-authority metadata.
