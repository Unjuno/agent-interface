# A01 — macOS 0.146.1 interrupt-transport portability check

## H/T/D/C/U (frozen before execution)

- **H:** The installed macOS arm64 Codex App Server `0.146.1` accepts `turn/interrupt` for a pending Responses turn, marks that turn `interrupted`, and admits a fresh same-thread text+PNG turn to the configured provider before a held first response is released, as observed on Windows App Server `0.160.0` in PR #8380/A06.
- **T:** Start the exact installed CLI binary in App Server stdio mode with a unique temporary `CODEX_HOME`, read-only sandbox, and an HTTP mock bound only to `127.0.0.1`. Hold response 1 after its `response.created` event. Send `turn/interrupt`, require the first turn's terminal status, then start a fresh same-thread turn containing a fixed text marker and valid 2x2 PNG data URI. Record whether request 2 reaches the mock before the explicit release barrier. Release response 1 at a finite 8-second bound, collect terminal/process receipts, and stop the mock. Run the candidate once; no retry.
- **D:** PASS only if the exact binary/version starts; only loopback Responses calls are observed; interrupt succeeds; turn 1 is `interrupted`; request 2 arrives before response 1 is released and contains both the exact text marker and PNG payload; turn 2 completes; App Server exits 0. FAIL if the protocol is exercised but any behavioral criterion is false. STOP if preflight/initialization/configuration cannot safely isolate the provider or exact installed binary/version is unavailable. Preserve any first-run failure without repeating it.
- **C:** The existing A06 is Windows x64 / Codex 0.160.0. This A01 changes both OS and App Server version, so it checks transport portability only; it is not a duplicate estimate of A06's same-host behavior. Successful interruption may discard useful inference work and requires another inference.
- **U:** One bounded probe on one macOS arm64 host and one older App Server build. This cannot establish model comprehension, latency/token savings, controller/V39 cancellation safety, useful live feedback, input release, recovery, or gameplay. No game, external provider, GUI, OS input, or private live allocation is involved.

## Frozen execution identity

- Parent: Issue #59; related prior result: PR #8380 A06.
- Candidate source: this package's `run_a01.py` (hash recorded in `SHA256SUMS` before execution).
- Independent auditor: this package's `audit_a01.py` (hash recorded before execution).
- App Server binary: `/opt/homebrew/bin/codex`, expected version `codex-cli 0.146.1`; binary SHA-256 recorded before execution.
- Host: macOS arm64; Python 3.14.5.
- Provider: ephemeral stdlib HTTP server bound to 127.0.0.1 only; no external provider/auth.
- Output: `results/a01/`; must be empty before the one candidate run.
- Scratch CODEX_HOME: fresh temporary directory outside the repository; preserve if generated files remain after process exit.
- Resource boundary: one local App Server process and one low-load loopback mock; finite waits and cleanup.
- Retry/stop: one candidate attempt only. No corrective rerun; any future correction requires a new frozen successor with new ID.
