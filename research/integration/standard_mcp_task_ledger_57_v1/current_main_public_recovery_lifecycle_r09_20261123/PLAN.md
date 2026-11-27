# R09 fresh lifecycle with callback-Future custody

## Question
Does the standard public Fake recovered-caller lifecycle meet its full exact-effect/recovery/oracle assertions over a new 5 normal + 5 `-O` fresh-process cohort, after test-side outstanding API Futures are tracked and drained before fixture teardown?

## Conditions
The server/runtime code and original 8-second callback / 10-second result-poll budgets are unchanged from R04. The only test harness delta is callback-Future diagnostics and bounded drain during teardown. Run the preregistered interleaved order in `conditions.json`, one process per sample. Pass requires exit 0, unittest OK, and all semantic assertions. No retries or replacements. R04 stays a separate historical cohort.

## Interpretation
This finite cohort measures only this Fake/local composed caller. It cannot establish native GUI, MAP01, production reliability, or comparative efficiency. A pass does not erase R04 failures.
