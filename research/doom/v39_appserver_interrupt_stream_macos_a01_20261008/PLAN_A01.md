# A01 — macOS pending-provider stream cancellation portability

## H/T/D/C/U (frozen before execution)

- **H:** On installed macOS arm64 Codex App Server `0.146.1`, `turn/interrupt` closes its pending HTTP Responses request to a loopback mock before the mock releases its held response. This tests the provider-socket cancellation boundary reported on Windows App Server `0.160.0` in PR #8077/A02.
- **T:** Launch the installed native CLI in stdio App Server mode with a fresh temporary `CODEX_HOME`, sanitized environment without user credentials, read-only thread sandbox, analytics disabled, and a mock bound only to `127.0.0.1`. The mock records one POST, sends `response.created`, then holds the HTTP stream. After the runner confirms the pending request, send `turn/interrupt` for the returned thread/turn IDs and wait for its RPC response. With no replacement turn started, watch the accepted TCP socket for EOF/reset for at most 2 seconds. Record completion notifications. At the bound, release the held response and perform bounded cleanup. One candidate run only.
- **D:** PASS only if the matching interrupt RPC succeeds, the first provider socket reaches EOF/reset before the response-release event, the matching turn completes as `interrupted`, exactly one Responses POST reached the loopback server, no server errors occurred, and App Server exits 0. FAIL if the RPC was accepted and turn completes but the request remains open through the pre-release window. HOLD if isolation, transport observation, or terminal receipt is incomplete. STOP if the installed CLI/version or isolated startup cannot be established. No retry.
- **C:** PR #8077/A02 already reports this behavior on Windows x64 / CLI 0.160.0. PR #8382/A01 showed a new observation request can reach a held stream on macOS 0.146.1 but did not observe whether the original stream closed. This experiment is a different outcome and a cross-platform/version replication, with no replacement turn before the primary closure window so closure is attributable to interruption itself.
- **U:** One bounded mock-only run on one macOS host/build. TCP closure to a local mock does not prove remote provider inference or billing stops. No model, game, GUI, OS input, V39 effect, useful feedback, physical release, recovery, progress, or gameplay is tested.

## Frozen identity

- Parent Issue #59; comparison PR #8077/A02; related transport-admission PR #8380/A06 and macOS replication PR #8382/A01.
- Source base: current `main` SHA `f72cd82d62c9d9f3860d4fa40980c56618bf5aaf`.
- Candidate and auditor source hashes, CLI binary hash, host/runtime, and output-empty preflight are recorded in `FREEZE.json` and `PRE_RUN_SHA256SUMS` before the one candidate run.
- App Server binary: `/opt/homebrew/bin/codex`, expected `codex-cli 0.146.1`.
- Output: `results/a01/`, absent before execution. Scratch state remains in a fresh temp directory outside the repo.
- Resource limit: one App Server process, one local mock, two-second pre-release observation bound; cleanup waits are bounded.
- No formal/live/game allocation; no API token or remote provider configuration; no retry.
