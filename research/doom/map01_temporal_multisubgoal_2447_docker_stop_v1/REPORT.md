# Issue #2447 construction boundary — Docker first rung

Status: **STOP — live MAP01 clock did not advance during passive wait**
Allocation: construction/environment only; no formal #2447 rows consumed.
Issue: https://github.com/Unjuno/agent-interface/issues/2447
Base main inspected: `75b3d1e9cf1518ed7912670ea541fe969b2fb0cd`.

## H/T/D/C/U

- **H:** A pinned, offline-capable Docker/X11 ViZDoom environment can host a fresh multi-subgoal MAP01 experiment while preserving the required live asynchronous clock, screen-only controller authority, current evidence and release semantics.
- **T:** Build a local-only Linux/amd64 image and smoke-import the inherited Python stack; attempt MAP01 with the wheel-bundled Freedoom WAD. Exercise ASYNC_SPECTATOR, ASYNC_PLAYER and SPECTATOR with passive wall-clock waits. Separately invoke `advance_action(35)` only as an engine responsiveness diagnostic, not as formal evidence. No GitHub Actions runner and no issue-specific formal cases.
- **D:** Proceed to experiment construction only if an asynchronous mode advances materially during a 1–2 second passive wait with no engine advance calls. Otherwise STOP; do not use forced advancing as a substitute. No efficacy decision.
- **C:** Docker Desktop Linux/amd64, `python:3.13-slim` pinned by digest; network disabled at runtime; issue-specific WAD/source bundle required for equivalence; controller input must remain X11/screen based. No hidden game state to the controller.
- **U:** This rung says nothing about temporal-gate correctness, subgoal sequence safety, failure injection recovery, or MAP01 completion. The bundled Freedoom content/runtime is only a construction fixture and is not the prior formal issue bundle.

## Frozen inputs and image

- Image tag: `agent-interface-map01-lab:2447-preflight-20260927`
- Image ID: `sha256:b99a3444e7b2b05d159976d9ba60d9e90f212d47406c4b7aa7773e5042a28713`
- Dockerfile SHA-256: `87f5e9b07ff66d7f55dab7441d5a60e0c559f27d627a311debac2dabc97d023a`
- Base: `python:3.13-slim@sha256:7c61056e61ac89e852de05f3dc6fa51a6dd2181797bceed46aa725dd7cb2cd3b`
- Runtime: Linux 6.6.87.2-microsoft-standard-WSL2, amd64, CPython 3.13.15, glibc 2.41.
- Packages: ViZDoom 1.3.0, NumPy 2.5.3, OpenCV 4.13.0, Pillow 12.3.0, pygame-ce 2.5.8, Python-Xlib 0.33, Gymnasium 1.3.0.
- Input offline source snapshot SHA-256: `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`; its manifest explicitly says `experiment_executed: false`, base commit `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`. It is NOT an Issue #2447 MAP01 WAD/source artifact.

## Executed outcomes

1. Docker build completed; a network-disabled, read-only import/version smoke check passed.
2. With the wheel-bundled `freedoom2.wad` (28,787,748 bytes), all three modes below stayed at their startup tic during passive wait:
   - ASYNC_SPECTATOR, 0.6 seconds: tic 1 → 1.
   - ASYNC_PLAYER, 1 second: tic 1 → 1.
   - SPECTATOR, 1 second: tic 1 → 1.
3. ASYNC_PLAYER with visible Xvfb/Openbox window and a 1-second passive wait stayed at tic 3 → 3.
4. ASYNC_SPECTATOR with visible Xvfb/Openbox window and a 2-second passive wait stayed at tic 3 → 3.
5. Diagnostic only: ASYNC_PLAYER `advance_action(35)` changed tic 1 → 54. This demonstrates engine responsiveness when explicitly advanced; it does not satisfy the passive live-clock criterion and was not counted as a pass.
6. A first read-only invocation failed because ViZDoom attempted to create `./_vizdoom/` and `_vizdoom.ini`; rerun with ephemeral tmpfs HOME/XDG paths reached the measured outcomes above. This setup failure is retained here, not erased.
7. The inherited #831 source proves only one fixed next Right 190ms action; its own report explicitly excludes generic multi-subgoal control. No #2447 formal comparison was run.

## Reproduction

Build (one-time local construction):
```powershell
docker build --tag agent-interface-map01-lab:2447-preflight-20260927 .agent-interface-docker-validation/issue2447/image-context
```

Offline import check:
```powershell
docker run --rm --network none --read-only --tmpfs /tmp agent-interface-map01-lab:2447-preflight-20260927 python -c "import cv2,gymnasium,numpy,PIL,pygame,Xlib,vizdoom; print(vizdoom.__version__,numpy.__version__,cv2.__version__)"
```

Passive wait checks used `docker run --rm --network none`, ephemeral tmpfs for HOME/XDG, SDL dummy or X11/Xvfb+Openbox, and read `DoomGame.get_episode_time()` immediately before and after `time.sleep()`; zero calls to `advance_action` occurred during those waits.

## Decision and next safe step

STOP at environment boundary. Do not run the #2447 temporal/endpoint/fail-closed arms in this image: the required continuously advancing experiment is not established. Preserve this first outcome. Next investigate why this container's ViZDoom runtime requires explicit engine advancement (compare against the project's known-good `research/observation_gating/gui_suite.py` session launcher and Docker settings) or obtain the exact MAP01 experiment bundle/runtime. After a passive clock probe passes, freeze the full H/T/D/C/U, at-least-three-subgoal schedule, independent effect/release scorer and fault controls before any formal allocation.

No performance, safety, multi-subgoal, model, product, or gameplay success claim is made.
