Exploratory command 1 (before selecting platform-compatible tests): `python -B -m unittest -v test_map01_overlap_controller_v39 test_map01_scorer_stdio_adapter_v1 test_session_map01_v15 test_doom_owner_thread_release_batch_backend_v1`.

Observed: V39 tests passed; the V15 anonymous-pipe test raised `WinError 10038` because Windows `select()` cannot wait on an anonymous pipe; the named `test_doom_owner_thread_release_batch_backend_v1` module does not exist. The test's writer then got `OSError: [Errno 22] Invalid argument` after the reader failed. No candidate/game process was launched.

Exploratory command 2 ran the V39, V15, and four scorer tests in one Python process. V39/V15 cases passed, but V15's legacy test harness left stub scorer modules in `sys.modules`, so four scorer tests failed with `TypeError: Sink() takes no arguments`. Running the V39, V15, and scorer test groups in separate fresh Python processes resolved this harness interaction; the final separate commands and passes are listed in `README.md`.

No failure was erased or relabeled as a candidate result.
