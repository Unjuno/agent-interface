# Experimental Calc lifecycle orchestration core

This is an incomplete, injectable orchestration prototype for the planned real-Calc comparison. It has no WSLc driver, Windows process-tree ownership, real scorer, GUI or model configuration. Do not use it to run live cells. Its caller/driver is trusted to implement identity tokens and its claimed audit and release receipts; mock results are not evidence of actual cleanup, input release, correctness or speed.

The core creates a fresh allocation directory, persists conditions, starts and waits through a driver, independently attempts host/container cleanup, separately records audit/release/cleanup, and marks a late zero exit incomplete. Execution and cleanup have separate budgets; a synchronous driver that blocks indefinitely can exceed them, and audit is not yet bounded. `before_result_write_ns` explicitly excludes final result serialization/write. Startup token preparation currently exists only in memory, not in a durable pre-spawn ownership protocol. Abrupt process death, conditions/result write failure, subprocess descendants, exact-CID binding, and partial-start reconciliation need a real design and tests before use.

Run the local fake-driver checks with:

```
python -m unittest discover -s research/integration/calc_lifecycle_core_r574_20261102 -p test_lifecycle_launcher.py -v
python -O -m unittest discover -s research/integration/calc_lifecycle_core_r574_20261102 -p test_lifecycle_launcher.py -v
```

No live allocation, model call, WSLc container or GUI was run for this prototype. The existing benchmark evidence and limits remain in `../calc_interval_scorecard_r572_20261102/`. The goal remains full measured task/release/recovery comparison, not completion of this helper.

The core checks a single execution deadline after the container wait and gives host/container cleanup a separate shared budget. It records late cleanup and refuses overall success, but synchronous start, cleanup and audit methods can still block beyond their budget; this is not a hard wall-clock bound. Driver return values are only minimally checked, and a driver-provided `release_confirmed` is trusted rather than independently authenticated. A concrete driver must persist ownership before resource creation, capture exact commands and raw diagnostics, validate CID/run identity, own the host process tree, supply bounded operations and an independent scorer, and distinguish absence from transport errors. No such driver exists here.

### Experimental exact-CID cleanup helper

`wslc_cleanup.py` is a standalone research helper, not a driver wired into `run_attempt` and not approved for live GUI/input use. It requires a caller-provided complete CID and unique `agent-interface.run-id` label. It checks the inspect identity and label and a full-ID positive listing before attempting a bounded stop; command output is retained as base64 in the returned receipt. Missing, malformed, timed-out or failing observations remain `UNKNOWN`. `observed_absent` means only that one successful exact-ID list was empty after a successful stop; it does not establish input release, task effect, process-tree termination, or general filter correctness. The caller must securely persist and redact receipts because inspect output may contain environment and mount data. The helper does not handle a partial or delayed CID file, a failed launch without a known CID, crashed Python process, host custody, or cleanup after its own deadline. Synchronous process creation and system calls are not independently proven bounded. Its fake-runner tests are not live WSLc evidence.
