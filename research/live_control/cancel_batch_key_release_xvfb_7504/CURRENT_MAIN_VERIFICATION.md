# Current-main verification — 2026-10-05

The rescue branch was refreshed onto current `main` commit `b5be19963454ce5edafc945b78b100012952dd15`. The merge completed without conflicts. The focused fake-Xlib tests were then rerun against the merged V10/V11/V13 sources on local macOS 27.0.1 / CPython 3.14.5:

- `test_explicit_up_owner_interval.py`: 2/2 passed in normal and optimized Python.
- `test_input_owner_v13_batch_release_telemetry.py`: 5/5 passed in normal and optimized Python.
- Existing `test_executor_owner_cancel_cause_v1.py` and `test_executor_release_publication_order_v1.py`: 2/2 passed in normal and optimized Python.
- `git diff --check` is clean for the updated source, focused tests, evidence package, and navigation.

The broader existing `test_input_owner_v13.py` module was not runnable in this host because PyXlib is not installed (`ModuleNotFoundError: Xlib`). No dependency was installed; the targeted tests use their own fake-Xlib boundary. Current-head hosted checks still need to finish.

The original candidate, old-source Xvfb smoke, and any live X server/input were not rerun. The interval remains an XTest request-through-existing-XSync bound, not a hardware transition or application-consumption timestamp. No gameplay, physical-key, recovery, or MAP01 claim follows.
