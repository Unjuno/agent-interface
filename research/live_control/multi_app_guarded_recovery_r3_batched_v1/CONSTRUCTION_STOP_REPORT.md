# Construction STOP report — Issue #3002

Status: formal allocation **NOT STARTED**. Formal rows: **0**. This is an OrbStack/arm64 construction-replication stop, not an R3 scientific FAIL and not a result against H.

The frozen upstream `common.py` and its three-cycle task semantics were not edited. Every attempted construction used a fresh session identifier and an isolated OrbStack/Docker container. Attempts 01–07 emitted no XTest key events. Attempts 01–02 stopped before finding Chromium; attempts 03–05 and 07 found Chromium but stopped before finding the peer XTerm window. Attempt 08 used a fresh session and added only `CAP_SETGID` to the otherwise dropped container capabilities; XTerm then stayed alive and the exact R3 code reached its first intended Ctrl+J shortcut. The observed Chromium page title differed from the frozen exact-effect gate, so construction stopped after that one shortcut. Nothing was retried within an attempt, no partial session was promoted, and no formal session batch exists.

## First outcomes

| Attempt | Session | Image ID | Outcome | Artifact SHA-256 |
|---|---:|---|---|---|
| 01 | 99 | `sha256:79611323b3e34ec26a3d1578761c83891598353fc7f64b95b986fe5ff9baf176` | `STOP_CONSTRUCTION_EXCEPTION: window_not_found:Chromium`; 0 input events; 3 process receipts | `ae64e335493ca11e55a1e94af3fb570514857c8b9af0e2b64bdff697b5d556e1` |
| 02 | 98 | `sha256:79611323b3e34ec26a3d1578761c83891598353fc7f64b95b986fe5ff9baf176` | `STOP_CONSTRUCTION_EXCEPTION: window_not_found:Chromium`; 0 input events; 3 process receipts | `91a7a9e35407f46307bea3ff80327168d0eb54e471429b7820e0ca0b801495e2` |
| 03 | 97 | `sha256:79611323b3e34ec26a3d1578761c83891598353fc7f64b95b986fe5ff9baf176` | `STOP_CONSTRUCTION_EXCEPTION: window_not_found:AI1769-PEER`; 0 input events; 4 process receipts | `a87fd6ea5c2152c55cfe3cdbb24c855ba84d42c67e76ca70927f53e4d2046860` |
| 04 | 96 | `sha256:dfc8716898572596038ac88414f27dfe3dd124d0bd60e8bff515aa4d29ad1a92` | Same peer-window STOP after adding `xfonts-base`; 0 input events; 4 process receipts | `180698ac1ee019a946921bec0f6ae3044f5cd4e68fe31ac36c7d8b5e47da6801` |
| 05 | 95 | `sha256:dfc8716898572596038ac88414f27dfe3dd124d0bd60e8bff515aa4d29ad1a92` | Same peer-window STOP; 0 input events; 4 process receipts | `c788542382dbdbbf210ad407ffe1ea8a5b8fec322fdb4b7a41d2381558e2980f` |
| 07 | 93 | `sha256:cb4e745a49e0ed05f6138d8608d9337028f30cd244c60f13063891782235f466` | Same peer-window STOP; 0 input events; 4 process receipts | `14648a11d81ee16ffbbbcfb2157b88dad6911ab024fdb81c27ba3c3539e574fd` |
| 08 | 92 | `sha256:dfc8716898572596038ac88414f27dfe3dd124d0bd60e8bff515aa4d29ad1a92` | `STOP_CONSTRUCTION_EXCEPTION: effect_title_missing:chrome://downloads/ - Chromium:Download history - Chromium`; first Ctrl+J XTest chord sent (4 edge receipts); 0 formal rows | `3415f2d59e09f888fa3812ae637f0ea38bc06ed262327e7c007467a0c15c7954` |

Attempt 02's retained Chromium stderr identifies a Crashpad startup error (`--database is required`). Attempts 03–07 retained empty `xterm.err`; the XTerm process exited 0 before the frozen code observed its titled window. Attempt 03 was the attempt whose retained XTerm stderr reported its default fixed font unavailable. Attempt 04 added Debian `xfonts-base`, but did not change the outcome. Attempt 07 used a separately built image with a font-path helper as container entrypoint; the frozen code created its own later display, so that helper did not resolve the peer-window issue.

After attempt 07, a separate Xvfb/Openbox/XTerm-only diagnostic ran `strace` on the exact `xterm -T ...` command. Its child-shell trace shows `initgroups failed: Operation not permitted`, followed by `xterm: Error 28, errno 1` and XTerm parent exit 0. This is consistent with the formal construction container's `--cap-drop=ALL` removing `CAP_SETGID`. Attempt 08 added only `--cap-add=SETGID`; XTerm became observable and the frozen R3 source executed Ctrl+J. It then observed Chromium 154's title `Download history - Chromium` where the immutable task expects `chrome://downloads/ - Chromium`. The original #1798 allocation used Chromium 144 on Linux/amd64 and passed its exact task-title gates. These are environment-specific observations; neither implies a defect in #1769 source.

Attempt 06 is intentionally absent: the output directory was not fresh, so the runner rejected it before launching any application (`STOP_CONSTRUCTION_OUTPUT_NOT_FRESH`). It is not an experiment outcome and has no result artifact.

## Preserved raw evidence

Each listed artifact is the complete canonical `CONSTRUCTION_STOP.json`; session-root files and process receipts are embedded as base64 with per-file byte count and SHA-256. Artifact paths are under `construction/orbstack-arm64-XX/`. The hashes above were recomputed from the retained files. Historical inputs in `upstream/` and each STOP artifact are immutable.

## Decision and next gate

## Relationship to the already integrated #1798 result

Current GitHub `main` already contains #1798's `PASS_MULTI_APP_GUARDED_RECOVERY_R3_DURABLE_A2_SCOPED`: the byte-identical #1769 science passed four fresh private-X11 sessions (48/48 refusal gates, zero-input refusals, active targets and exact effects; 12/12 replacements; 4/4 neutral terminals), with eight independent corruption controls. That result exercises the same durability hypothesis with four once-only batch commands inside one logical formal allocation. It satisfies the substantive H of #3002; this branch's single-process wrapper is a different collection implementation, not a reason to duplicate the scientific formal allocation. #1798's retained scope remains Linux/amd64, Chromium 144; it does not claim arm64/Chromium 154 portability.

Decision for this OrbStack/arm64 replication: **STOP_CONSTRUCTION_EFFECT_TITLE_MISMATCH** after resolving the XTerm capability issue. Do not start a new #3002 formal allocation: the scientific H is already answered on main, and this local attempt reached a separately observed exact-title incompatibility. A future portability experiment would need its own issue/freeze and may not change the #1769 task/effect gates.

The local batch-contract suite passed 3/3. It tests source-hash binding and file-write/canonical-JSON mechanics only; it does **not** validate X11 construction, R3 behavior, session batching in a formal run, or any scientific hypothesis. The six initial STOP hashes above were recomputed from the retained canonical files; attempt 08's hash was likewise computed from its raw artifact.
