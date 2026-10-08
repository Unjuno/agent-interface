# Host runner caller result (#2558)

This artifact records the first fresh call through the existing
`integrated_efficiency_model_v1.call()` path with
`AGENT_INTERFACE_MODEL_RUNNER=host_codex_exec_runner_v1.py`. The retained
Docker-native observation image was supplied to the host-local `codex.exe`
boundary and the response passed the existing compiled grounding validator.

No input was emitted. The grounding coordinates are model output only; the
runtime must still perform fresh focus, geometry, pixel, and effect checks.
