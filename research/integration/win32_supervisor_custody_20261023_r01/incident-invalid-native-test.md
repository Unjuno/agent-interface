# Invalid native integration test execution — not qualification evidence

The broad command accidentally run was:

```text
python -m unittest runtime.backends.win32_v1.test_supervised_session runtime.backends.win32_v1.test_integration runtime.backends.win32_v1.test_release_ledger runtime.backends.win32_v1.test_explicit_up_ledger runtime.backends.win32_v1.test_unknown_release_custody runtime.backends.win32_v1.test_process_identity runtime.guarded_win32_v1.test_process_cancellation runtime.guarded_win32_v1.test_operation_owner runtime.cli_v1.test_mcp_win32_composition
```

Observed failure excerpt:

```text
FAIL: test_valid_program_has_independent_effect_capture_and_release (runtime.backends.win32_v1.test_integration.Win32IntegrationTests.test_valid_program_has_independent_effect_capture_and_release)
...
self.assertGreater(self.backend.emissions, before)
AssertionError: 0 not greater than 0
Ran 87 tests in 23.604s
FAILED (failures=1)
```

This Windows-only class launches the repository fixture GUI and invokes the native backend. The emissions counter recorded no successful backend emission before the assertion, but this alone does not establish that no native API call or fixture-side effect occurred. A subsequent process query found no process whose command line contained `runtime.backends.win32_v1.fixture_app`; the fixture class cleanup was expected to close it. The run is excluded from every pass count and all qualification claims. Do not rerun it. The exact captured failure excerpt is retained here; the original command output was not redirected to a file at execution time.
