# Tk keymap refresh after XKB layout change

## Question and scope

Successor experiment for [Issue #4664](https://github.com/Unjuno/agent-interface/issues/4664), testing the Tk boundary excluded from predecessor Issue #4557. In six fresh Xvfb sessions, does an already-running Tk window translate X keycode 29 according to the server's current German mapping after one US-to-DE XKB layout change?

**H — Hypothesis:** in the declared Linux ARM64/Xvfb/Tk environment, the existing Tk window and a newly created Tk window both translate keycode 29 as `z` after the server changes from US (`y`) to DE (`z`).

**T — Minimum discriminator:** one fixed allocation of six fresh Xvfb sessions. Each observes US server/Tk baseline, changes the server layout once, reads back the server map, then injects an XTEST press/release into the old and fresh Tk windows. A separate X connection checks server key-down state. No retries or replacement sessions.

**D — Decision:** `PASS_TK_XKB_REFRESH_SCOPED` only when all six sessions are complete and auditable, old and fresh Tk both report `z`, events are balanced, key state is neutral, and frozen-source/process/raw-log checks are clean. `FAIL_TK_STALE_MAPPING_EXPOSED` if any complete clean row shows server `z`, fresh Tk `z`, but old Tk not `z`. Otherwise HOLD.

**C — Competing explanations:** a stale event queue, input delivered to the wrong window, incomplete XKB propagation, or stuck key state could mimic a refresh result. The harness therefore gates on phase/window identity, server-map readback, balanced XTEST requests, independent server state, neutral terminal state, and clean process exits.

**U — Uncertainty:** result is limited to this immutable Linux ARM64 container, Python 3.12.3, Tk/Tcl 8.6, Xlib 0.33, Xvfb, keycode 29, and one US-to-DE transition. It does not demonstrate behavior on native display servers, other Tk/Xlib builds, other keys/layouts, or integrated applications.

## Result

**PASS_TK_XKB_REFRESH_SCOPED**, six of six sessions; no stale mapping observed. Every session observed US server/Tk `y`; after the layout change, server mapping was `z` and both the existing and fresh Tk windows reported `z` on press and release. Independent server observation showed key-down after press and key-up after release; final key state was neutral. Xvfb exited 0 in all sessions. Fixture processes were intentionally terminated after capture and their signal exits recorded. No retries, replacements, or timeouts.

The independent audit returned `errors=[]` for all six rows and `stale_mapping_observed=false`. Runtime packages: Python `3.12.3-0ubuntu2.1`, python3-tk `3.12.3-0ubuntu1`, Xvfb `2:21.1.12-1ubuntu1.6`, xauth `1:1.1.2-1build1`, x11-xkb-utils `7.7+8build2`; setxkbmap 1.3.4 and xkbcomp 1.4.6.

## Reproduction and evidence

Run `run_formal.py` only against the exact declared image and only for a new, explicitly frozen allocation. The formal run for this report is retained under [`evidence/formal-01/`](evidence/formal-01/). It includes source snapshots, the frozen manifest, six raw session directories, orchestration, runtime inventory, and per-file hashes. `evidence/formal-01/audit.json` is the independent verdict.

- Frozen manifest SHA-256: `593cc891a8d347ebb4466492f4d88afca9f9c9ef90931084d41740ead0685455`
- Evidence hash manifest SHA-256: `c6b672525de474f77ed501b4d5638457dd3cb044c898c78bafde66f9b0cc8185`
- Independent audit SHA-256: `022c4cc0a120c8a5befd8e81e862b6e2cacb8b11073c3a6f32c6b4d43020a39b`
- Image: `sha256:4c62a3d908f6bffdbff88b28eeff305bed40f5d6fcee029b7c0a3fa2ea5a86d6` (`linux/arm64`)
- GitHub record: [Issue #4664](https://github.com/Unjuno/agent-interface/issues/4664)

Construction attempts are not in the formal denominator. They are discussed in the Issue thread; the final mechanics-only construction record remains separately retained there and locally.

## Validation

The host and immutable OrbStack container each passed the 27 synthetic auditor tests before formal allocation. The host suite also passed after the formal run. `py_compile` and `git diff --check` passed. Synthetic tests validate the decision/audit machinery and are not experimental observations.
