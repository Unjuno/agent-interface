# Successor runner status

The successor runner is present at `research/container_control/typed_deadband_postcondition_successor_v1/typed_deadband_runner.py`.

Status: IMPLEMENTATION ADDED / EXPERIMENT NOT RUN

The runner is mechanically derived from the retained v3 rendered Tk/X11 fixture. It exposes `--deadband` and uses the typed threshold for admission and guard cancellation. The historical v3 runner is unchanged.

Required next action:
- execute in an isolated Linux/Xvfb container;
- retain the first outcome without retry;
- add raw manifests and an independent audit;
- record PASS, FAIL, or HOLD_NO_REQUIRED_EXPOSURE in a separate report.

No scientific or safety claim follows from the code addition alone.