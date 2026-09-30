# X11 window-relative region across window moves — successor allocation v2, Issue #4902

Predecessor Issue #4439 allocation `x11-region-frame-move-4439-localdocker-v1-20260927` is frozen STOP before formal case 0. Its one runner invocation failed because a Docker bind-mount pre-created `/out`, which the frozen runner requires creating itself. It produced zero raw rows and zero X11 sessions. Preserve that record unchanged: [predecessor STOP receipt](https://github.com/Unjuno/agent-interface/blob/research/x11-region-frame-move-4439-20260927/research/observation_gating/x11_region_frame_move_q5t2_v1/FORMAL_01_STOP.json), [predecessor branch](https://github.com/Unjuno/agent-interface/tree/research/x11-region-frame-move-4439-20260927).

This successor corrects only the mount contract and uses a new additive allocation/path. Hypothesis, source, treatment matrix, quality gates, and limits are unchanged.

## H — hypothesis

For the same live X11 window XID and immutable target-relative pixels, a pinned initial screen rectangle is stale after a move; refreshed root translation works if the move precedes resolution but fails if the window moves between resolution and capture; direct `WINDOW_CLIENT` capture remains bound to the same window content in all three schedules. Mismatch is stale-coordinate observation, not target absence or action authority.

## T — frozen allocation

- 3 policies (`PINNED_SCREEN`, `REFRESH_SCREEN`, `WINDOW_CLIENT`) × 3 schedules (`STABLE`, `MOVE_BEFORE`, `MOVE_BETWEEN`) × 3 repetitions = **27 first-outcome sessions**. Each owns a fresh private authenticated TCP-disabled Xvfb and one override-redirect 120×80 Xlib window at (20,20), moved to (220,160) when scheduled. Candidate captures use no semantic labels; scoring-only oracle reads the same window XID after candidate capture.
- Local cached image `agent-interface-string8-4638:candidate-v1`, immutable ID `sha256:1c334ebd65f4b1bfe81cc84c90780ea01e6f70c0f7b18cd89c09e03406460238`, linux/amd64, Python 3.11.16, Debian 13.7, Python-Xlib 0.15, Xvfb 21.1.16, Xauth 1.1.2. No Tk libraries; use direct Xlib fixture and make no Tk claim. No network/pull; source/root read-only; `/tmp` bounded private tmpfs; runner 1 CPU/512 MiB/64 PIDs. The X11 capture mechanism is CPU-bound; GPU is deliberately unused.
- Frozen runner SHA-256 `6c7d86c6ffc3c3bbcce45086fe52572d36267b5cc5b0647711a3db43c3f2d17c`; independent raw-only auditor SHA-256 `a3cdb1ea959deccca87b9a7f2387f754cedd624426caf358cdf5726b13743c97`. The auditor re-hashes/decompresses retained candidate/oracle/exposed pixels, regenerates schedule/coordinates, checks Xvfb/authority receipts and applies 14 copied corruption controls.
- Correct invocation contract: mount source at `/study:ro`; mount an existing writable host **parent** directory at `/out-parent`; pass a nonexistent child `/out-parent/formal01` to runner. Runner creates that child. Never mount the intended child itself. Auditor runs in a separate offline container with `/study:ro` and the parent mounted; reads `/out-parent/formal01/raw.jsonl` and writes `/out-parent/audit01.json`.
- Each row keeps candidate, oracle and exposed pixels as deterministic gzip+base64 with hashes/lengths; geometry, candidate capture monotonic bracket, Xvfb PID/exit/log hashes and Xauthority file mode. Runner fsyncs each completed row.

## D — frozen decisions

`PASS_X11_REGION_FRAME_MOVE_BOUNDARY_SCOPED` requires 27/27 unique sessions; correct frozen geometry and candidate coordinate receipts; every mapped target image differs from pre-map black background; STABLE all 9 matches; MOVE_BEFORE PINNED_SCREEN 0/3 and other policies 3/3; MOVE_BETWEEN WINDOW_CLIENT 3/3 and both root-coordinate policies 0/3; all candidate/oracle/exposed/background bytes and hashes reconcile; every process exits 0 and authority mode is 0600; independent audit errors empty and all 14 corruption controls reject. Complete contrary coordinate evidence is `FAIL_COORDINATE_FRAME_PREDICTION`; any source/image/process/coverage/pixel/audit discrepancy is HOLD/STOP. One invocation only, no retries, replacements, post-result tuning, exclusions, or pooling.

## C — confounds

No window manager/compositor; cooperative mapped opaque window with fixed pixels; serialized XConfigureWindow + XSync moves. This measures X11 server ordering and direct window-relative capture. Root capture may see explicitly repainted exposed background. Does not test asynchronous races, natural miss rates, semantic identity, occlusion, destroy/recreate, resize, Wayland/compositors, or pixel freshness at later model consumption.

## U — limits

One synthetic X11 window, Docker image, and host. Not evidence for Tk, all apps, backend correctness, semantic targeting, action safety, task correctness, latency savings, model utility, or production readiness. Same-author raw auditor is not independent human review.

Execution sequence: successor plan/source and corrected invocation read back from GitHub → one local 27-session invocation → separate local raw audit → immutable STOP/PASS/FAIL report and exact raw/audit publication → additive PR → exact-head checks/review. No external workflow is used for experiments.
