# POSIX test portability follow-up

The four mocked process-group methods in the current regression module now use the same POSIX-only skip condition as the real process-tree tests. This prevents `patch(os.killpg)` from failing during test setup on platforms without `os.killpg`; it does not change POSIX test behavior or production code.

The original `RESULT.json` and its `test_sha256` are unchanged and continue to identify the historical test source used for the repair result. This separate follow-up applies only to test portability.

The current module passed 8/8 on Darwin CPython 3.14.5 in normal and optimized modes. No Windows runner was available; Windows skip behavior is stated from the standard `unittest.skipUnless(os.name == \"posix\")` guard and remains unexecuted on Windows. No research allocation, model, GUI, or runtime experiment was rerun.
