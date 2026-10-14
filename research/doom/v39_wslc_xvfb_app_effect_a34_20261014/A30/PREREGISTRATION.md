# Preregistration: V39 WSLc X11 application effect and expiry recovery A30

Experiment ID: `MAP01-V39-WSLC-XVFB-APP-EFFECT-A30-20261014-01`
Source main: `014bd4279a716d376f167e14fadc418f57e558f7`
Allocation: one foreground WSLc container, unique name `map01-v39-wslc-a30-20261014-01`, one candidate invocation and one saved-raw audit. The output path must not exist before launch.

## H / T / D / C / U

**H.** The current main V39 composition (`InputOwner V4 → V3 → V12`) will deliver one admitted `a` key to a focused X11 test application. The application will change a server-visible counter from 0 to 1. When the 300 ms lease expires, the owner will emit a matching KeyRelease, record a known-empty release accepted by the exact mainline V39 strict release predicate, and stop cleanly after close.

**T.** Start one Xvfb server at display `:143` inside a WSLc container with network disabled. Use separate X11 connections for the application, owner, and property/keymap verifier. Send exactly one `a` down through V4. The application increments `_A30_TASK_COUNTER` on the matching KeyPress. Do not send an explicit up or cancellation: let the fixed lease deadline exercise the owner’s expiry recovery. Record the admission receipt, target-window KeyPress and KeyRelease, cross-connection property values, server keymap, owner release records, timings, and process cleanup. Run the candidate once, then run the independent saved-raw auditor once.

**D.** PASS only if (1) the exact V4 owner admission receipt matches key, owner, and intent; (2) the focused target window receives the matching keypress; (3) a second X11 connection observes counter `0 → 1` within 200 ms of input acknowledgement and still observes `1` after release; (4) the same window receives the matching key release within 1,000 ms after the 300 ms lease deadline; (5) a second X11 connection reports the key up; (6) the owner’s `reason=expired` receipt is accepted by the frozen `terminal_release_is_known_empty` function with empty unknown/error fields within 1,000 ms of deadline; (7) the owner closes and its thread stops; (8) Xvfb exits 0; (9) all frozen-source checksums match. A failure after input dispatch is FAIL. A setup/preflight stop before input dispatch is HOLD. Preserve every first outcome; no rerun or threshold changes.

**C.** The outcome may depend on Xvfb scheduling, focus/event routing, XTest delivery, or the toy application. A single synthetic run is a boundary check, not an efficacy comparison. The counter may establish only this test application's response, not a Doom action or useful gameplay feedback.

**U.** No game, MAP01, model call, physical keyboard, Windows desktop application, threat response, survival, or real task completion is included. XQueryKeymap verifies X-server state only. One latency observation is not a distribution or a hard-real-time guarantee. WSLc may report the memory limit without swap enforcement.

## Frozen conditions

- Image ID: `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592` (`a09-owner-close-xvfb:20261012`), pull policy `never`.
- Network `none`; 1 CPU; memory limit 1 GiB; no GPU; container removed at process exit.
- Read-only source and X11 runtime binds; writable output parent only; UID `user` for Python; root only for loopback setup and the temporary `xkbcomp` symlink.
- Unique X display `:143`; private container loopback only; X11 Unix sockets disabled.
- Lease 300 ms; app feedback bound 200 ms; expiry release and verified-release bounds 1,000 ms each.
- Image, source hashes, WSLc version, runtime-package hashes, commands, raw output, and audit are stored alongside this preregistration.
