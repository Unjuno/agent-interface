# Safety-plane dependency inventory successor #2256

This additive rung performs a source-first inventory of the current-main kernel/CLI safety path named by #2256. It is not a runtime fault-injection experiment.

## Scope

Pinned sources are runtime/kernel/contracts.py, runtime/kernel/lifecycle.py, and runtime/cli_v1/api.py. The audit extracts imports, lifecycle boundary calls, release/cleanup symbols, and explicit authority-bearing types from Python AST without importing or executing the runtime.

## Result boundary

The audit may establish only that the declared source-level dependency inventory is reproducible and that runtime fault-injection remains unexecuted. It does not establish graph completeness, wall-clock release, actuator safety, hidden IPC/display/scheduler dependencies, or task safety. Those remain HOLD requirements for #2256.

Run:

```bash
python audit.py
```

Expected result: `HOLD_RUNTIME_FAULT_INJECTION_REQUIRED`.
