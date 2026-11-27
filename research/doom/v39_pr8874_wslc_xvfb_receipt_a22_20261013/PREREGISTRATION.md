# Production-adapter-shaped V39 one-key receipt integration A22

## Hypothesis, test and decision

**Question:** When the real `doom_owner_thread_release_batch_backend_v1.py` emits its down admission and batched up transition through the real current-main V4/V12 owner, do those exact published rows satisfy the unchanged current PR #8857 retained-input analyzer?

**One-shot test:** private TCP-disabled Xvfb, focused observer window, one lowercase `w` through the backend's unmodified `raw()` and `_flush_pending_ups()` / `_publish_release_batch()` methods, one independent Xlib KeyPress/KeyRelease watcher plus XQueryKeymap samples. `emit()` mirrors the session JSONL behavior by retaining the exact row and adding emit timestamp. Analyzer runs over those exact emitted rows. WSLc candidate invocation once; no retry.

**PASS_METHOD_SCOPED:** matching same-key/window event pair, server keymap down/up, admission row owner-bound by backend, V4 explicit-up and owner transition verification, analyzer ready with one hold, owner cleanup stopped and empty, Xvfb exits 0, independent source/raw audit matches. Verified X11 key-up plus analyzer rejection is `FAIL_ANALYZER_BRIDGE`; setup defect is `STOP`.

## Scope and deviations

The adapter source, its `raw`, `_flush_pending_ups`, and `_publish_release_batch` implementations are exercised unchanged; the actual game-specific base backend lifecycle is not instantiated. The test injects only an abstract parent class because the map/game dependency is unavailable in the cached Python Xvfb image. A real V4/V12 owner and real Xvfb/XTEST still perform the input. This is a backend-to-analyzer composition test, not a full Doom session.

No physical keyboard, desktop application, Doom/MAP01 task result, threat exposure, model call, or live/formal allocation. One synthetic X11 key only. Requested memory is not claimed as a hard cap due unsupported host swap/cgroup limits.

## Frozen inputs

Backend source hash is in `SOURCE_MANIFEST.json` and matches current `origin/main` and PR #8874. Owner files are exact A09 current-main-frozen sources at base `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. Analyzer is exact current PR #8857 head `cd766747abb4ca6d321b626c0a7b9734b9e06816` and byte-identical to the A21 analyzer copy. WSLc 3.0.1.0, Python 3.14.8 linux/amd64, immutable image `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`, no network, one CPU, source read-only, separate output, UID 65534, `--rm`.

Only output leaf: `results/a22-01/`; container `codex-wslc-v39-backend-xvfb-a22-20261013`.
