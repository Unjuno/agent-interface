# Allocation 01 stop

Outcome: `STOP_BEFORE_INPUT`. The container started private Xvfb, but the runner failed during its initial import before `NativeHandleBridge` construction or fixture-process start: `ModuleNotFoundError: No module named 'runtime'`. Root cause was the invocation adding `/app/runtime` rather than its parent `/app` to `sys.path` for the `runtime.*` namespace package.

No fixture/client, alias, stale-guard decision, or native input was executed. This allocation is terminal and will not be retried. Empty stdout, stderr and Xvfb logs are retained beside this record. A separate allocation with a corrected invocation receives a new freeze and output path.
