# Construction log

- Frozen six schedules and separated candidate-visible input from evaluator-only effect truth.
- Before freeze: 4/4 tests passed on Python 3.12 and 3.14, normal and optimized.
- Watched the positive/negative assertions exercise the queued control, identical emitted views, neutral release, request binding, and mutation rejection.
- Source freeze committed at `c16c8a57a5e2a2598b3bae94f50d65f631f2dedf` before allocation invocations.
- Post-freeze: candidate once, auditor once, retries zero. Both exited 0; see `RUN_RECORD.json` and retained `results/`.
