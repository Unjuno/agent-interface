# WSLc bounded cancellation recovery on Xvfb A27

## H/T/D/C/U

- H: After one backend-owned key is held on Xvfb, cancelling the active lease will revoke input and produce a same-key KeyRelease and server keymap-up within 2 seconds, without replaying the queued UP. Terminal release will verify empty input state, stop cleanly, and clear the admission cache.
- T: One offline WSLc run. Use the exact current workspace V39 backend and A09 current-main V4/V12 owner. Focus one Xvfb window; admit one w down; independently observe KeyPress and keymap-down; set lease cancellation; invoke backend raw-up once; wait for matching KeyRelease; query keymap; call terminal release; save owner records, latency, disposition, and cleanup. One candidate invocation; no retry.
- D: PASS_METHOD_SCOPED requires matching KeyPress/KeyRelease, keymap down then up, recovery at most 2 seconds, verified empty owner_release(reason=cancelled), no explicit per-key UP receipt because queued UP was cancelled and not attempted, verified terminal cleanup, empty admission cache, stopped owner, Xvfb exit 0, source audit pass, and WSLc cleanup. Missing release or uncertain state is FAIL. Setup failure before input is STOP.
- C: XTEST/Xvfb proves virtual server state only. Cancellation is injected directly and is not a model-latency or live visual-guard event.
- U: No desktop app, game/MAP01, task effect, threat exposure, model call, or live/formal allocation. This tests cancellation recovery only.

The run uses WSLc 3.0.1.0, immutable cached image sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592, Python 3.14.8 linux/amd64, no network, one CPU, read-only source, separate output, UID 65534, and --rm. Host swap/cgroup memory enforcement is unsupported; no hard memory cap is claimed. Full source hashes are in SOURCE_MANIFEST.json. Output leaf: results/a27-01; container name codex-wslc-v39-cancel-xvfb-a27-20261013.
