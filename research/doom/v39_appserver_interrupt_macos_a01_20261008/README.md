# App Server interrupt portability check — A01

## Result

**Scoped PASS** on macOS arm64 with installed Codex CLI/App Server `0.146.1` (`/opt/homebrew/bin/codex`, SHA-256 `35d248101b211d6248ad4e6b8c1d441fe81236da87afb9f3e9ea51a049e9f179`). With a loopback mock Responses API holding its first stream response, the App Server accepted `turn/interrupt`, reported the first turn as `interrupted`, and sent a fresh same-thread text+PNG request before the runner released that held response. The new turn completed; there were exactly two loopback Responses requests; App Server and runner both exited 0. The independent v2 audit passed 12 checks and five mutation controls.

This is a cross-platform/version replication of the explicit-interrupt A06 in [PR #8380](https://github.com/Unjuno/agent-interface/pull/8380), which used Windows x64 / Codex 0.160.0. It reduces the uncertainty that this transport behavior is unique to that one build. It remains one bounded probe on one Mac and one older binary.

The runner's barrier receipt says the second request arrived before `release_first.set()`; the frozen runner source confirms that the event wait precedes the release call. A race prevented `first_response_released_at` from being copied into `result.json` before result assembly, so there is no separate release timestamp. A01 v1's strict audit therefore failed that check, and its request parser also expected a different input shape. Both failures are retained in `results/a01/audit.json` and `audit_v1_runner_exit.txt`. Retained-result audit v2 re-parses the redacted request summary, validates the PNG, checks the recorded event barrier against the frozen source order, and accepts the missing wall-clock comparison with this explicit limitation. No candidate rerun was made. Absolute UTC start/end timestamps were not captured by the runner; the retained request times are process-local monotonic values only.

The initial `PRE_RUN_SHA256SUMS` verification was also invoked from the wrong directory and failed to find package-relative paths; the corrected package-local verification passed all five frozen files. This procedural error is retained in `results/a01/pre_run_integrity.json`.

## H/T/D/C/U

- **H:** Codex App Server 0.146.1 on macOS arm64 supports the same explicit interruption boundary observed on Windows App Server 0.160.0: interrupt a pending Responses turn, then admit a fresh same-thread observation turn before the held first response is released.
- **T:** One candidate run with isolated temporary `CODEX_HOME`, read-only sandbox, sanitized process environment, and stdlib mock bound to `127.0.0.1`. The first response was held behind an event; after `turn/interrupt` and the first turn's terminal event, a second turn carrying a fixed text marker and valid 2x2 PNG was sent. No retry.
- **D:** PASS requires version/binary identity, interrupted first turn, fresh same-thread turn reaching the mock before release, exact marker and PNG, completed second turn, two mock requests, and zero process exits. The v2 audit reports scoped PASS with five mutation controls.
- **C:** The probe establishes transport scheduling only. Interrupting discards the previous inference and starts another one; it may cost time and tokens. Different versions/providers may differ. The result does not measure net latency.
- **U:** It does not establish V39 cancellation safety, model comprehension or useful feedback, per-key input release, recovery, progress, terminal outcome, or gameplay. The private live lane remains unassigned in Issue #59.

## Reproduction and privacy boundary

Pre-run frozen source identities are in `FREEZE.json` and `PRE_RUN_SHA256SUMS`. The one candidate command was `python3 run_a01.py --out-dir results/a01`; the independent audit commands were `python3 audit_a01.py results/a01` (v1, retained fail) and `python3 audit_a01_v2.py results/a01` (v2, scoped pass). Run the v2 audit self-test with `python3 audit_a01_v2.py --self-test`.

The full mock request capture (`results/a01/requests.json`) remains in this local worktree and is excluded from Git. App Server had injected Codex host instructions and skill metadata into the request body. `redact_requests.py` emits the published whitelist-only `requests_redacted.json`, which retains endpoint/loopback evidence and only the synthetic observation marker and 2x2 PNG while omitting injected instruction text. No credentials or external provider were configured.

App Server stderr was not retained for this A01, so it cannot establish that the process made no unrelated startup network requests. A separate later probe with the same installed binary recorded a request to the featured-plugin metadata endpoint, returning 401 (see [PR #8388](https://github.com/Unjuno/agent-interface/pull/8388)). Whether that occurred during A01 is unknown. This does not change the observed local Responses requests, but it limits any zero-egress interpretation.

The installed native macOS App Server binary was required for this compatibility check, so it could not be moved into a Linux container without changing the tested client. No game, external model/provider, GUI, OS input, or live allocation was used. No runtime/controller code changed. Issue #59 remains open; this does not close its live threat, release, useful-feedback, recovery, progress, and terminal-outcome gate.
