# PR #9247 private-Xvfb server-stop recovery run

- GitHub Actions run: https://github.com/Unjuno/agent-interface/actions/runs/39398154419
- Run artifact: https://github.com/Unjuno/agent-interface/actions/runs/39398154419/artifacts/12253645651 (`standard-mcp-xvfb-server-stop`)
- Tested head: `544af3a12c37b7d1aa6b171ce7a9302892e836ab`
- Scope: owned standard MCP caller; workflow-owned private Xvfb stop/resume; synthetic application; fresh-target recovery.
- Result: `FAIL`. The original outage task remained `UNKNOWN`; Xvfb resumed and explicit final close eventually verified keys up, but runtime cleanup stayed `UNKNOWN`, task success stayed null, and the independent oracle failed.
- Recovery-specific failure: `interface_guarded_mint` refused alias `recovered-field` because the API permits `[a-z][a-z0-9_]{0,31}`. The fresh action was not attempted. Follow-up head `0cb355de20f7bcafdaa9655b8843f791c015aa79` changes the alias to `recovered_field`; it requires a new Linux/Xvfb run.
- Separate suite failure: `test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb` observed `owner_release_attempt.status=unknown` (`worker_did_not_exit_cleanly`, exit `-15`) rather than `readback_verified`. Preserve this as an independent unresolved boundary; do not weaken the assertion.
- On Windows, the affected module ran 5 tests with 1 Xvfb test skipped in both normal and `python -O` modes.
- GitHub displayed the run as `in_progress` after the Xvfb step had already failed and artifact upload completed. A cancel request finalized the stale run state; the test result is preserved in the log/artifact.
- SHA-256 of the JSON below: `558813ca7bc9db7e665857e09b7275ece48ae76ff677dbbe61326bef4e0c0ae2`.

This receipt preserves a failed run; it does not claim recovery works. It is synthetic evidence only and says nothing about physical input, MAP01, WSLc, live control, or efficiency.