# Issue #4588 confidence-trajectory first rung

This evidence package records two distinct, model-free synthetic allocations:

- [`confidence_trajectory_first_rung_v1/`](confidence_trajectory_first_rung_v1/)
  — `FAIL_INTEGRITY`; scenario timing was not paired as claimed. Preserve this
  failure and its original source unchanged.
- [`confidence_trajectory_first_rung_v2/`](confidence_trajectory_first_rung_v2/)
  — matched clocks/noise and passing alias controls, but
  `HOLD_NOOP_STALL_RISK` / `HOLD_ACCEL_NOT_BETTER_THAN_VELOCITY`; do not promote
  to real caller-visible shadow or live action.

These allocations are synthetic mechanism probes for
[Issue #4588](https://github.com/Unjuno/agent-interface/issues/4588), not
runtime changes, GUI measurements, or product claims. Each version contains
its frozen source, preregistration, and result; v2 also contains a structured
transcription of the emitted metrics JSON.
