# #1876 A2 formal stop — ordered interrupt batching

Decision: **`STOP_FORMAL_OUTER_TIMEOUT_NO_RESULT / scientific NONE`**.

The A2 import-scope repair passed `py_compile`, the unchanged 10/10 unit tests, a one-case smoke check, source freeze/readback, and ownership reread. Its first and only formal invocation then exceeded the outer 120-second command wrapper before `FORMAL_RESULT.json` serialization.

- formal invocations: 1
- reruns/replacements/tuning: 0/0/0
- durable scientific rows: 0
- `FORMAL_RESULT.json`: absent
- stdout: 0 bytes
- residual `run_formal.py` / `audit.py` processes after stop: 0

No scientific PASS/FAIL is inferred from elapsed time or partial in-memory work. #1871 remains a separate pre-row import-binding stop; no rows from either predecessor are pooled.

A legal successor may change exactly one harness factor: formal execution/durability packaging. The batch size, event schema, directed cases, exhaustive sequence corpus, prefix checks, metadata semantics, malformed controls, negative comparator and scientific decision gates remain fixed.
