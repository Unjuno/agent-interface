# Issue #2849 child-process import preflight v25

Seed 284925 verifies inherited `PYTHONPATH` for the runner's child process inside the pinned outer image. It performs imports only: no fixture preparation, socket server, GUI, task token, broker, or model call.
