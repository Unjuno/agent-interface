# Task-1 successor v4: host-broker schema-preflight STOP

Decision: **STOP_BEFORE_TASK_EXECUTION**. No model, GUI, input, authority, or task-effect result is claimed.

## H/T/D/C/U

- **H**: the pinned host executable and container route can pass schema preflight for one task-1 request.
- **T**: one bounded allocation using the pinned image and frozen source hashes in `preregistration.json`; container and IPC request were created, and schema preflight was reached.
- **D**: `RESULT.json` preserves the recorded stop; the immutable issue history is at [#2813](https://github.com/Unjuno/agent-interface/issues/2813). The corresponding source-pin verifier is retained, but running it against current main is a freshness check, not a replay of the historical allocation.
- **C**: continuation required a resolved host executable and a valid schema response. The broker could not resolve the container working path; no model invocation followed.
- **U**: the retained record does not establish a task result or diagnose later runtime/effect behavior. The next attempt must use a new preregistered allocation.

This historical STOP is preserved as recorded; it is not replaced by later task-1 successor results.
