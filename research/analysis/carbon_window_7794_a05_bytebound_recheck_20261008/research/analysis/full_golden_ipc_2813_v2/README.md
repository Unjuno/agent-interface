# Full golden IPC task-1 successor entry gate

Successor preregistration for Issue #2813. The original `full_golden_ipc_2813_v1`
record is retained unchanged. This snapshot updates only the source pins to the
current checkout, including the bounded host-broker timeout and startup-error
reporting changes. It is an entry gate only: no model, GUI, input, or task
execution is authorized by this check.

Disposition is `PASS_TASK1_ROUTE_PREFLIGHT` only when every source pin matches;
the subsequent container allocation must record `HOLD_DOCKER_UNAVAILABLE` if
the Docker Linux engine is unavailable.
