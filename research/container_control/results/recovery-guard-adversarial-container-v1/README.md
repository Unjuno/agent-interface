# Reproduction

Run in a disposable Python 3.13 container. No network, GUI, model, or OS-input dependency is required.

```bash
python3 research/container_control/recovery_stress_v1.py
sha256sum /tmp/recovery_stress_v1.json

python3 research/container_control/recovery_deadband_stress_v1.py
sha256sum /tmp/recovery_deadband_stress_v1.json
```

Expected full-result SHA-256 values from the retained execution:

- `/tmp/recovery_stress_v1.json`: `ced529209d7844e64add2b8ba26c1aac4993f8f8b59dc1a4221cf5ba7f8e6007`
- `/tmp/recovery_deadband_stress_v1.json`: `2913eb66902c2602cf73895037d193041457e3825755de67ccf66c84e7f7c049`

The JSON includes wall-clock runtime and therefore direct file hashes are environment-sensitive if runtime differs. The scientific rows are deterministic from the frozen seeds; `sha256_without_sha_field` is calculated before adding that digest but still includes runtime. Use the retained `summary.json` for the published small result and compare row values rather than treating wall-clock runtime as scientific state.

Scope: synthetic guard falsification only. This does not authorize a MAP01 live allocation or modify the formal recovery preregistration.
