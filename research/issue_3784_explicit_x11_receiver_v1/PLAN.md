# Issue #3784 — explicit X11 receiver allocation

## H / T / D / C / U

**H** — The prior zero-event result came from an unverified receiver window/focus/selection arrangement. An explicitly mapped X11 `InputOnly` receiver selecting `KeyPress|KeyRelease`, with its focus read back, will receive an independent XTEST `a` control and then the frozen backend's exact `=B2*A2` output under the standard German XKB map. Unsupported trailing `€` will be rejected with no events or emissions.

**T** — One allocation, `issue3784-explicit-x11-receiver-formal-01`: three fresh private Xvfb `-noreset` German rows and one US control. In each row, create/focus the receiver and require the XTEST control before candidate input; retain US baseline and after-layout server query, `xkbcomp` dump, and map from a fresh Xlib connection. German rows apply exactly `setxkbmap -layout de`. Refuse `=B2*A2€` during backend preflight, then plan and emit `=B2*A2` once. Record all events with keycode/state and `XLookupString`, planned keycode trace, emission count, release state, immutable source hashes and cleanup. Run the independent auditor in a second no-network container. No retry.

**D** — PASS only if all 3 German rows and US control independently confirm the requested server map, receiver focus and receiver-only XTEST control; unsupported text is refused with zero events/emissions; exact candidate formula and full planned press/release trace arrive; release state is empty; and the separate audit verifies source and artifact integrity. Unconfirmed setup is STOP/HOLD. Wrong text, extra/missing events, release failure or failed unsupported preflight is FAIL. A PASS is only the combined pinned-image, Xvfb `-noreset` plus continuously connected explicit receiver condition; it does not attribute causality to either factor individually.

**C** — OrbStack Docker Engine on Linux/arm64, image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, `--network none`, read-only source/root, isolated writable output. No host display/input, GUI app, install, or model. Candidate source is bound to base `f319d64a0de28ba765f86772123308e3d96baac2`; backend blob `9cae101a219348077668c8fc086acf8e13154afe`.

**U** — Exact frozen X11 backend, Xvfb and standard German two-level XKB only. No Calc/task effect, physical keyboard, IME/Compose/dead-key/level-3, other layout/backend, latency, or product claim.

## Construction gate (not formal evidence)

Pinned-container test `construction_test.py` creates one private Xvfb, maps and focuses an InputOnly window with the exact key event mask, sends one XTEST `a` press/release, and verifies both received events and `XLookupString`. Result: 1/1 pass. This tests the receiver mechanism only and is not counted toward the four formal rows.

## Freeze

- Base: `492279afebf6a0bafc31fb1e1558c53805761c0d`
- Runner SHA-256: `bb202694699595887735b9121324b402751c5171087ad993853dde4cde2b1e9e`
- Source manifest SHA-256: `a75320185da90945ebca6b442df4972b032c687c6f8710a5aa4856f41ddc9374`
- Auditor is separately implemented and writes only to the audit output mount.
