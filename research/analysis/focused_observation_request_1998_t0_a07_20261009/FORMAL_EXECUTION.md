# Formal execution record

The frozen formal wrapper was invoked once under network-denial sandbox:

```
/usr/bin/sandbox-exec -p '(version 1) (allow default) (deny network*)' /opt/homebrew/opt/python@3.14/bin/python3.14 research/analysis/focused_observation_request_1998_t0_a07_20261009/formal_runner.py
```

Wrapper exit: 1. Candidate invocation: 1, exit 0. Auditor invocation: 1, exit 1. Retries: 0. Candidate raw stdout and stderr, auditor raw stdout and stderr, and `RUN.json` are retained under `results/`.

The candidate emitted 22 rows (candidate-reported counts: two `FULL_FRAME`, two `DECLARED_FOCUS`, and 18 `REFUSE`). The auditor failed inside its own corruption-control mutation before producing an audit result: it attempted list-style mutation on an immutable string pixel row and raised `AttributeError`. This is `HOLD_AUDITOR_RUNNER_ERROR`; no independent scientific disposition is available. Candidate output is preserved but is not promoted to a validated result. A07 is consumed and will not be rerun.
