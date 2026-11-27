# Formal execution record

The frozen wrapper was invoked once under network-denial sandbox:

```
/usr/bin/sandbox-exec -p '(version 1) (allow default) (deny network*)' /opt/homebrew/opt/python@3.14/bin/python3.14 research/analysis/focused_observation_request_1998_t0_a08_20261009/formal_runner.py
```

Wrapper exit: 0. Candidate invocations: 1 (exit 0). Independent auditor invocations: 1 (exit 0). Retries: 0. Candidate stdout is 15,478,472 bytes; exact candidate/auditor stdout, stderr, exit codes, and hash-bound run record are retained under `results/`.

The auditor independently reconstructed 27,664 cases: 16 `FULL_FRAME`, 16 `DECLARED_FOCUS`, and 27,632 `REFUSE`; its disposition is `PASS_METHOD_SCOPED` with no errors. All six mutation controls were rejected by newly introduced, specific audit errors. See `RESULT.json` and `OUTPUT_SHA256SUMS.txt`.
