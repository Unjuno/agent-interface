# Issue #4536 deterministic clock-domain regression

This additive offline test isolates whether a host-monotonic hard policy
invalidation can be compared safely with a runtime-monotonic controller
decision. It preserves the host receipt, translates with the conservative
lower bound from three same-session probes, and tests fail-closed behavior for
wrong-domain, missing provenance, stale/future, malformed, and over-wide
calibration inputs.

The deterministic regression does not run a model or admit motor input. It
uses the preserved decision-8 clock probes and terminal/controller timestamps;
the missing historical invalidation time is explicitly synthetic and cannot
prove the predecessor's causal boundary. An independent zero-model preflight
did run the pinned runtime, complete observe-only controls, and record three
verified empty owner releases. This is startup/release evidence, not gameplay
or proof of release causality for a rejected planner action.

Run locally:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v research.doom.map01_policy_invalidation_clock_4536_v1.test_clock_translation
```
