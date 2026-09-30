# Qwen 0.5B safety-class support study — terminal STOP

Issue #4988 preregistered a paired GPU study of balanced versus predecessor-shaped support sampling. Its single formal invocation exited during runner preflight because `run_formal.py` read the formal input digest from the wrong JSON level. It stopped before model load, with zero fit/evaluation steps and zero GPU memory use. The preregistration forbids retries, so this allocation is terminal and has no scientific model result.

- `STOP.md`: reason and decision record.
- `formal.stdout.log`: unmodified Docker runner exception and exit status.
- `preflight.txt` and `postflight.txt`: host GPU and container observations.

The corrected study is tracked independently in successor Issue #5014 with fresh allocation and seeds.
