# Post-merge native-MCP compatibility regression

This is a follow-up to the synthetic compiled-caller packet. PR #9212 merged,
then its `native-mcp` workflow exposed a real compatibility regression:
`GuardedSessionOwner.snapshot()` attempted to publish `compiled_scope` for every
non-null bridge. The established `FakeBridge` used by ordinary guarded MCP tests
has no compiled scope, so 42 cases in `runtime.cli_v1.test_mcp_guarded` failed
(41 errors and one assertion failure). The compiled route itself requires the
real scoped bridge; optional summary fields must not break existing bridge
implementations.

The exact downloaded GitHub artifact is preserved in this directory, including
`native-ci/result.json`, stdout/stderr for the protocol, harness, and Win32
suites, and the artifact's companion `primary-owner/` raw receipts. At
the failing PR head, the Linux/Python 3.12 runner reports 660 protocol tests
with 41 errors and one failure, while the 254-test harness suite and 56-test
Win32 suite pass (eight native-Windows cases skipped). The protocol stack trace
identifies the missing `FakeBridge.scope` attribute.

The follow-up fix now adds compiled metadata only when `bridge.scope` is a
nonempty string. Local Windows Python 3.11 verification of
`runtime.cli_v1.test_mcp_guarded` passes 43/43 in both normal and optimized
mode. A broader attempt to run `runtime/integration_checks/native.py` locally
is also retained at `../local-native-followup-r01/`: this Windows host lacks
`os.O_DIRECTORY`, and the runner's default cp932 console encoding cannot print
one Unicode replacement character after the first suite. That attempt is not a
passing full-suite result and is not evidence against the Linux root-cause
reproduction.

This is a scoped repair of a post-merge compatibility regression. The Fake X
limits in the parent packet remain unchanged; no live-control, task-success,
release, MAP01, or efficiency conclusion follows.
