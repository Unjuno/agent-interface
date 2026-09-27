# Issue #3792 — explicit receiver oracle correction and German formula delivery

## H / T / D / C / U

**H** — With the observed XTEST control oracle corrected to accept XLookupString `a` on both KeyPress and KeyRelease, a fresh focused receiver will receive the current-main X11 backend's exact `=B2*A2` under standard German XKB and the US control. Public `X11Backend.preflight` will refuse a trailing unsupported `€` with zero backend emissions and receiver key events.

**T** — One allocation, `issue3784-explicit-x11-receiver-formal-02`, on exact main source base `d685f881cb5050bc42b6b96007978df9f532fe78`; candidate blob `9cae101a219348077668c8fc086acf8e13154afe`. Four fresh private Xvfb `-noreset` servers: three US-baseline→German rows and one untouched US control. Create/map an InputOnly receiver selecting KeyPress|KeyRelease, set and read back focus, and emit a receiver-only XTEST `a` control. Advance only if the exact observed control is KeyPress `a`, KeyRelease `a`, with XLookupString `a` for both. Confirm US baseline query, server dump, and fresh-client map. On each German row, call `setxkbmap -layout de` once and capture query/dump/fresh-client map. Run public backend preflight on `=B2*A2€`, require U+20AC refusal with zero emissions/events; run public preflight on valid formula and require zero emissions/events; then run planner and emit the formula once. Record every event, keysym/state/XLookupString, planned keycode trace, emission/release state, phase, hashes, and cleanup. Use a second no-network container for independent audit. No retry or mutation of this allocation.

**D** — PASS only if all three German rows and US control confirm the requested server map, focus, and receiver-only XTEST control; unsupported public preflight refuses with zero events/emissions; valid preflight is zero-emission; actual received formula and full planned press/release trace match; release state is empty; source and artifact integrity pass independent audit and every corruption challenge is rejected. Wrong text/trace, premature event, preflight emission, or release failure is FAIL. Setup, harness, or audit integrity defects are STOP/HOLD and never candidate PASS/FAIL. A stop before map capture must not require nonexistent map artifacts; report the reached phase.

**C** — OrbStack Docker Engine 29.4.0, Linux/arm64; immutable image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`; `--network none`, read-only root/source/harness and isolated writable output mounts. No host display/input, GUI application, package install, model, or application data.

**U** — Exact candidate X11 backend, private Xvfb, and standard German two-level XKB only. No Calc/task effect, physical keyboard, Compose/dead-key/IME/level-3, other backend/layout, latency, or product claim.

## Formal freeze

- Source base commit: `d685f881cb5050bc42b6b96007978df9f532fe78`.
- Candidate blob: `9cae101a219348077668c8fc086acf8e13154afe`.
- The source manifest binds six runtime files by Git blob SHA-1 and SHA-256.
- Construction test is run before formal allocation and is not formal evidence.
- Formal output is `results/formal-02/`; independent audit output is `results/audit-02/`. Both must be empty. Never clear, reuse, or rerun either output.
- Runner, auditor, plan, source manifest, image digest, output directories, and invocation hashes are frozen before the formal container starts.
- Frozen runner SHA-256: `40ce0dca6bb04ab54305bbe9001c52b34600a5479dc50b8acde871009fa0751f`; source manifest SHA-256: `b5aafca39bd927098c7074f8dbdd12e46b34c3b6f908505cbdbef54f0ebbf7e5`.
- The independent auditor additionally binds these runner and manifest hashes; audit code is hash-checked and frozen with the experiment commit.
- Formal host stdout/stderr and independent audit stdout/stderr are saved separately under `results/host/`.
