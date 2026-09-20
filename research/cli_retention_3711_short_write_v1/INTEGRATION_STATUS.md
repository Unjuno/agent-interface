# Integration status — Issue #3711 short-write construction

Checked 2026-09-21 JST. The frozen source protocol in `PROTOCOL.md` is
historical and unchanged; it says no result was claimed when written.

## Implementation and checks

- PR #3727 merged the short-write detection and regression changes to
  `runtime/cli_v1/__main__.py` and `runtime/cli_v1/test_attempt.py`.
- PR #3729 merged explicit flush handling and its regression; byte-preserving
  recovery is still the intended behavior.
- Windows and macOS `cli` jobs passed in both recorded workflows. The Ubuntu
  `cli` job failed in both: 88 tests ran with three errors in
  `runtime.selector_v1.test_selector.SelectorTests.test_explicit_display_selects_and_opens_same_x11_without_mutating_environment`.
  Each error was `AttributeError: module 'runtime.backends' has no attribute
  'x11_v1'` while the selector test patched that import path.
- The failing jobs are [PR #3727 run](https://github.com/Unjuno/agent-interface/actions/runs/35527038747)
  and [PR #3729 run](https://github.com/Unjuno/agent-interface/actions/runs/35527161406).

## Disposition and limits

The protocol required the full Runtime CLI workflow to pass on Ubuntu,
Windows, and macOS. Because the Ubuntu job failed, that preregistered
cross-platform construction gate is **not PASS**. The logs identify selector
mock/import errors, not a reported short-write assertion failure; therefore
they do not establish that the short-write behavior itself failed either.
Keep the protocol result as `INCOMPLETE_CROSS_PLATFORM_CI` pending the Ubuntu
test-import issue; do not infer a three-OS PASS from the merged implementation
or from Windows/WSL results alone.

This protocol covers a mocked short-write construction case, not an induced
OS pipe truncation or live consumer disconnect. Issue #3711 remains open for
its other gates. No local Docker, GUI, model, native input, or live-application
allocation is claimed here.
