# Relay JSON boundary successor

Status: HOLD for Linux CI and independent review. This report records a fresh
ordinary engineering regression run on current `main`; it does not claim a live
GUI, task-effect, latency, model, or formal-allocation result.

## Lineage and scope

- Baseline: `main` at `25700c9f68e9937fc1057a5da91d14c3971bb2b6`
  (2026-10-04 08:54:02 +09:00).
- Original work: branch
  `fix/relay-finite-json-01a0ff58-20261003`, commit
  `e71aea05be766718412d0e003a6cd3f9de9b69c1`, open draft PR #6879.
  Its source ref and historical results were left untouched.
- Successor candidate: commit `59cf3ad0710c370b56aa34ef1fd2b042e68bc93b`
  on an additive local branch based on the baseline above.
- No backend/input action, GUI session, research allocation, Docker workload,
  or model invocation was made.

H: valid JSON exponent overflow can decode to infinity; duplicate members,
unpaired surrogate escapes, malformed/non-UTF-8 pipe bytes, and decoder
recursion can otherwise cross relay admission or terminate the relay. Locale
text wrappers can also corrupt UTF-8 JSON-lines transport.

T: compare fresh requests against an inert MCP-shaped client, preserving
valid finite-number and Unicode controls, duplicate-key controls at envelope
and nested levels, malformed UTF-8/UTF-16/UTF-32, deep and moderate nesting,
same-ID continuity after refusal, accepted-call uncertainty/no-replay, and a
portable zipapp process outside the checkout.

D: invalid input must be refused before SDK entry and ID consumption; accepted
calls consume IDs before SDK entry and are never replayed. Valid representable
values and Unicode scalar strings must remain unchanged. Pipe bytes must use
UTF-8 independent of locale.

C: downstream SDK/schema validation does not establish pre-SDK refusal. The
mocked unit boundary is not a real application effect. Existing historical
source/SDK evidence remains separate and unchanged.

U: this does not establish arbitrary JSON depth/memory limits, application
success, GUI reliability, performance, or a formal candidate result.

## Results

- Test-first RED on current main: 18 tests discovered, 31 expected failures,
  zero test errors after repairing the fixture and matching the current relay
  response schema. Failures covered nonfinite overflow, duplicate keys,
  surrogate inputs, excessive nesting, UTF-8 pipe/locale behavior, and the
portable process path.
- Successor unit run: `python -m unittest runtime.cli_v1.test_mcp_relay -v` —
  18/18 passed. The portable test rebuilt from the committed successor source,
  ran outside the checkout, and exercised refusal/ID continuity.
- Native MCP local integration command
  `python runtime/integration_checks/native.py --output
  /tmp/agent-interface-relay-native-ci-20261004` — overall FAIL on macOS.
  Protocol suite: 459 tests, 4 failures, 6 errors, 5 skips; the 18 relay tests
  passed. Harness suite: 205 tests, 31 errors. Failures include Linux-only
  `/proc/self/ns/pid` assumptions and macOS `/private/var` path canonicalization
  in unrelated allocation, receipt, and path-identity tests. No full local-CI
  PASS is claimed; obtain the repository's Linux CI result before merge.
- Native host relay regression command from `.github/workflows/native-mcp-v1.yml`
  — Node 22, 199/199 passed.
- Independent review/approval for this changed tree and a passing Linux CI
  result are still required. No merge or source-branch deletion has occurred.

The native integration runner's raw local logs were emitted under `/tmp` and
are not committed; its result JSON at that path identifies both suites and
their return codes. The original #6879 evidence archives remain the custody
source for predecessor runs.

## Change

`runtime/cli_v1/mcp_relay.py` now strictly decodes pipe bytes as UTF-8, rejects
nonfinite decoded floats, decoded duplicate object keys, lone surrogates, and
decoder recursion before dispatch, and writes pipe responses as UTF-8 bytes.
Text-stream compatibility remains for in-memory/dev callers without `.buffer`.
Focused tests and the portable relay documentation were updated accordingly.
