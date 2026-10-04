# Executed command and environment

From the repository root, with the current PR #7376 source checkout:

```sh
python -B research/live_control/owner_admission_marker_lifecycle_5156_v1/run_capture.py
```

The capture command runs `run_probe.py`, retains stdout/stderr in
`results/RAW_PROBE.txt`, and records its actual exit status in
`results/EXIT_CODE.txt`. Environment: Python 3.12.13;
`macOS-27.0.1-arm64-arm-64bit`. No container or external service was used.

Afterward, the following local checks passed:

```sh
python -B research/live_control/owner_admission_marker_lifecycle_5156_v1/audit.py
python -m unittest research.live_control.test_input_transition_owner_v3 research.live_control.test_input_transition_owner_v3_owner_queue
python -m py_compile research/live_control/input_transition_owner_v3.py research/live_control/input_owner_v10.py research/live_control/test_input_transition_owner_v3.py research/live_control/test_input_transition_owner_v3_owner_queue.py research/live_control/owner_admission_marker_lifecycle_5156_v1/run_probe.py research/live_control/owner_admission_marker_lifecycle_5156_v1/run_capture.py research/live_control/owner_admission_marker_lifecycle_5156_v1/audit.py
git diff --check
```
