# Task-1 successor v5: host/container path-namespace STOP

Decision: **STOP_BEFORE_TASK_EXECUTION**. No model, GUI, input, authority, or task-effect result is claimed.

## H/T/D/C/U

- **H**: the host-broker bridge resolves the container's declared paths and reaches a valid schema preflight for one task-1 request.
- **T**: one bounded allocation using the pinned image, wrapper, and source hashes in `preregistration.json`; the container and IPC request were created, and schema preflight was reached.
- **D**: `RESULT.json` preserves the recorded stop; the full subsequent task-1 history is in [#2813](https://github.com/Unjuno/agent-interface/issues/2813). The absolute local executable path in the original preregistration is redacted here; other source pins and the result are unchanged.
- **C**: the host bridge only mapped `/repo` while the container published `/workspace`, so the host could not resolve the schema/working directory. No model invocation followed.
- **U**: this path-mapping STOP does not establish task behavior or acceptance. Later fresh successors are separate evidence and do not rewrite this allocation.

The paired `verify_preregistration.py` checks historical hashes against the current checkout; a mismatch is expected when source has since advanced and must not be mistaken for a replay of this allocation.
