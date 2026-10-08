# Construction record

Formal cases executed: 0.

1. First unit-test invocation used `python -I -S -B test_policy.py`; isolated mode intentionally removed the study directory from `sys.path`, producing `ModuleNotFoundError: policy`. This is a wrapper/import construction failure, not a scientific result.
2. The same frozen policy/test bytes were then executed from the study directory with `python -B test_policy.py`: 7/7 unit tests passed.
3. Environment preflight: CPython 3.13.5; both `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME` are available. A diagnostic pair of readings showed both clocks callable in this container.

No application-event formal child process has been started. The formal command will be frozen after GitHub readback of the exact source hashes.
