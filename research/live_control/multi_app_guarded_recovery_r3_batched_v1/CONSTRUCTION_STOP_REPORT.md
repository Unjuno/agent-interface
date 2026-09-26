# Construction STOP report — Issue #3002

Status: formal allocation **NOT STARTED**. Formal rows: **0**. This is an environment/construction stop, not an R3 scientific FAIL and not a result for H.

The frozen upstream `common.py` and its three-cycle task semantics were not edited. Every attempted construction used a fresh session identifier and an isolated OrbStack/Docker container. No key-input events were emitted. The first two attempts stopped before finding Chromium; four later attempts found Chromium but stopped before finding the peer XTerm window. Nothing was retried within an attempt, no partial session was promoted, and no formal session batch exists.

## First outcomes

| Attempt | Session | Image ID | Outcome | Artifact SHA-256 |
|---|---:|---|---|---|
| 01 | 99 | `sha256:79611323b3e34ec26a3d1578761c83891598353fc7f64b95b986fe5ff9baf176` | `STOP_CONSTRUCTION_EXCEPTION: window_not_found:Chromium`; 0 input events; 3 process receipts | `ae64e335493ca11e55a1e94af3fb570514857c8b9af0e2b64bdff697b5d556e1` |
| 02 | 98 | `sha256:79611323b3e34ec26a3d1578761c83891598353fc7f64b95b986fe5ff9baf176` | `STOP_CONSTRUCTION_EXCEPTION: window_not_found:Chromium`; 0 input events; 3 process receipts | `91a7a9e35407f46307bea3ff80327168d0eb54e471429b7820e0ca0b801495e2` |
| 03 | 97 | `sha256:79611323b3e34ec26a3d1578761c83891598353fc7f64b95b986fe5ff9baf176` | `STOP_CONSTRUCTION_EXCEPTION: window_not_found:AI1769-PEER`; 0 input events; 4 process receipts | `a87fd6ea5c2152c55cfe3cdbb24c855ba84d42c67e76ca70927f53e4d2046860` |
| 04 | 96 | `sha256:dfc8716898572596038ac88414f27dfe3dd124d0bd60e8bff515aa4d29ad1a92` | Same peer-window STOP after adding `xfonts-base`; 0 input events; 4 process receipts | `180698ac1ee019a946921bec0f6ae3044f5cd4e68fe31ac36c7d8b5e47da6801` |
| 05 | 95 | `sha256:dfc8716898572596038ac88414f27dfe3dd124d0bd60e8bff515aa4d29ad1a92` | Same peer-window STOP; 0 input events; 4 process receipts | `c788542382dbdbbf210ad407ffe1ea8a5b8fec322fdb4b7a41d2381558e2980f` |
| 07 | 93 | `sha256:cb4e745a49e0ed05f6138d8608d9337028f30cd244c60f13063891782235f466` | Same peer-window STOP; 0 input events; 4 process receipts | `14648a11d81ee16ffbbbcfb2157b88dad6911ab024fdb81c27ba3c3539e574fd` |

Attempt 02's retained Chromium stderr identifies a Crashpad startup error (`--database is required`). Attempts 03–07 retained empty `xterm.err`; the XTerm process exited 0 before the frozen code observed its titled window. Attempt 03 was the attempt whose retained XTerm stderr reported its default fixed font unavailable. Attempt 04 added Debian `xfonts-base`, but did not change the outcome. Attempt 07 used a separately built image with a font-path helper as container entrypoint; the frozen code still chose its own `:91` display and XTerm still exited without a window. Do not infer a single root cause from these observations.

Attempt 06 is intentionally absent: the output directory was not fresh, so the runner rejected it before launching any application (`STOP_CONSTRUCTION_OUTPUT_NOT_FRESH`). It is not an experiment outcome and has no result artifact.

## Preserved raw evidence

Each listed artifact is the complete canonical `CONSTRUCTION_STOP.json`; session-root files and process receipts are embedded as base64 with per-file byte count and SHA-256. Artifact paths are under `construction/orbstack-arm64-XX/`. The hashes above were recomputed from the retained files. Historical inputs in `upstream/` and each STOP artifact are immutable.

## Decision and next gate

Decision: **STOP_CONSTRUCTION_ENVIRONMENT_UNRESOLVED**. Do not start the four-session formal allocation from this environment. Next action is a non-formal, logged diagnosis of why XTerm exits 0 without a managed window under the exact frozen Xvfb/Openbox stack; any changed launch environment must get a fresh image identity and one excluded construction first. Only a fully observed construction with all original gates and cleanup checks may authorize preregistration and the single formal invocation. No retries, replacement sessions, or pooling are authorized by this report.

The local batch-contract suite passed 3/3. It tests source-hash binding and file-write/canonical-JSON mechanics only; it does **not** validate X11 construction, R3 behavior, session batching in a formal run, or any scientific hypothesis.
