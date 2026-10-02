# Shared owned public dispatch integration 01

The persistent MCP route previously set `owner.dispatch_attempted` before calling
the ordinary public API. Direct Python callers had to reproduce that bookkeeping.
A missing flag could skip same-connection release during close after an uncertain
input attempt. `MCPSessionOwner.dispatch` now owns that obligation; MCP uses the
same entry point. The ordinary one-shot and compiled-graph routes are unchanged.

Base source: 882e1ef41208cd4422f22648b446ce9b3fff08af. The candidate changes are
retained in this integration commit, not retroactively applied to frozen studies.
The API report is returned unchanged, the supplied program/source/capture options
are forwarded once, and exceptions propagate to the existing transport handler.
A mismatched or boolean binding revision refuses dispatch, though connection
initialization can already have occurred, matching the persistent route's ordering.
No implicit inspection, replay, lease issuance/renewal or recovery reset is added.

## Evidence

- `red.stderr`: missing dispatch method fails the uncertain-emission cleanup test
  before implementation. This test simulates the API exception boundary.
- `final-targeted.json` and corresponding logs: six added owner-entry tests plus
  existing session/post-capture tests pass normally and under Python `-O`.
  Cases cover exact report preservation, mismatch, boolean revision, closed owner,
  exceptions and consumed initialization failure. Mocked tests do not prove GUI
  task effects or actual held-key fault recovery.
- `native_smoke.py` and `native-smoke/result.json`: one fresh private Xvfb :287
  allocation in Ubuntu. Actual public dispatch sends `a`, then `b` to an explicitly
  registered fixture window. A second, independent X11 connection receives exactly
  the two expected press/release pairs. An injected API response loss after the
  completed second input propagates without replay. Close attempts one additional
  same-owner release, reports verified neutrality, is idempotent, and the owned
  Xvfb exits 0. This is a mechanics probe; the fault occurs after completed input,
  not during a physically held key. No model or application task is benchmarked.
- `native-checks/result.json` and hashed full logs: complete existing native
  protocol/harness suites, run without Docker. Read actual test counts in stderr.

## Adoption scope

Promote shared bookkeeping for serialized persistent Python/MCP callers. Cleanup
remains best effort and reports failure. No concurrency, automatic fallback or
implicit source refresh is introduced. Separate compiled connections retain their
own input-owner obligation. Caller-written low-level `dispatch_in_session` remains
available; bypassing the owner method requires the caller to manage its own cleanup.

No matched model task, first useful feedback, semantic completion, provider token,
cost, memory or human-tempo improvement has been measured here. The integration
removes a duplicated caller responsibility; it does not establish those benefits.
