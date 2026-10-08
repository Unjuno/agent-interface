# Pre-freeze runner setup attempt

Before A01 was frozen, the V39 suite was invoked from the exported source root
without adding `research/live_control` to `PYTHONPATH`. It stopped at import
with `ModuleNotFoundError: No module named 'running_action_guard_v1'`. The
owner-admission and bridge suites in that same setup attempt passed 3/3 each,
but this partial run is not A01 evidence and is not pooled into its result.

The setup defect is addressed prospectively in the frozen A01 command by
adding both `research/doom` and `research/live_control` to `PYTHONPATH`. The
original tool output remains in the Codex task record; A01's own exact outputs
and exit codes will be retained separately.
