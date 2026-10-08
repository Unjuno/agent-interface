# formal02 STOP — host setup failed before candidate dispatch

Allocation: `5260-a15-model-paired-formal02-20261004`

The preflight passed, but the trusted exchange-host process exited immediately
at `HostBridge` initialization. The configured custody directory
`_research_5260_a15_formal02_20261004/host` had been created in advance to hold
launcher receipts; `HostBridge` correctly requires that directory not to exist
and creates it itself. This was an orchestration setup error, not a WSLc or
container restriction.

No candidate container, GUI, exchange slot, or provider request was started.
The host traceback and launcher attempt metadata are preserved under `host/`.
This allocation is stopped and will not be retried or edited into a successful
run. A unique successor allocation uses a separate launcher-log directory and
leaves the host-owned custody directory absent until the bridge starts.
