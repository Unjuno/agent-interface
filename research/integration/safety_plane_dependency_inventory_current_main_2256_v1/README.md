# Safety-plane dependency inventory — current-main successor

This additive successor revisits #2256 against the current `main` source
blobs. It performs an AST-only dependency inventory and deliberately does not
claim runtime fault-injection, timing, actuator, GUI, model, network, or
production evidence.

Status: `HOLD_RUNTIME_FAULT_INJECTION_REQUIRED`.

Current-main observation: `runtime/cli_v1/api.py` exposes `open_session` and
`dispatch` calls in the audited facade; no `close` call is present in this
source blob. This is recorded as an observation, not as evidence that cleanup
is complete.

Run from the repository root:

```text
python research/integration/safety_plane_dependency_inventory_current_main_2256_v1/audit.py
```
