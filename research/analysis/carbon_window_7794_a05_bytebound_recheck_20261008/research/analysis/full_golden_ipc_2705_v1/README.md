# Full golden route over container-host model IPC (#2705)

This is an additive preregistration for successor Issue #2705. It preserves
the frozen #57/#2068 route and results. The allocation is one fresh,
no-retry run; a failed preflight, IPC timeout, rejected grounding, missing
receipt, stale reuse, effect mismatch, or cleanup failure is retained as
FAIL/HOLD rather than repaired or selected away.

The GUI/runtime remains in the pinned Docker image. Model calls cross the
shared-volume IPC runner/broker to the PC-local `codex.exe`. Model output is
never authority; ordinary target admission and independent effect scoring stay
mandatory.
