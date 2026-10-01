# Preregistration — same-window GTK pixel stability calibration

Parent: [#4466](https://github.com/Unjuno/agent-interface/issues/4466), itself a successor to [#3240](https://github.com/Unjuno/agent-interface/issues/3240) / [#2850](https://github.com/Unjuno/agent-interface/issues/2850) / [#2606](https://github.com/Unjuno/agent-interface/issues/2606).

## H / T / D / C / U

**H — hypothesis**

The retained #3240 target-window XWD transition from 247 RGB colors to all-black pixels was caused by target/decoy overlap or capture validity rather than an application state effect. In a fresh no-input session, three repeated same-window XWD captures will be RGB-identical while the GTK target is unobscured; three captures while an identical-size/title decoy is stacked above it will return an all-black target image; after moving the decoy to an adjacent non-overlapping position the target RGB image will return to its original value. Window identity, map state, geometry, stacking request, focus and root active-window state will distinguish capture visibility from a task effect.

**T — frozen formal schedule**

One fresh private Xvfb session, one GTK target and one render-only GTK decoy, all in the pinned image. Fixed sequence, with 250 ms waits between samples:

1. Capture target XWD three times with only the target present.
2. Start the same-title/same-size decoy at the same `(0,0)` position, request X11 `ConfigureWindow(stack_mode=Above)`, and capture target then decoy three times.
3. Move only the decoy to `(400,0)` on an 800×400 root, request `Above`, synchronize X11, and capture target then decoy three times.

Retain every XWD byte, raw SHA-256, mask-aware RGB SHA-256, unique RGB color count, changed-pixel count/bounding box, monotonic capture time, XID/PID/title/class, full geometry, `Map State`, root tree, focus and `_NET_ACTIVE_WINDOW`, decoy move request/sync receipt, effect/event file presence and process cleanup. The independent auditor parses the raw XWD bytes; it does not import the runner. A separate auditor self-test must reject capture-count/order corruption and detect one changed RGB pixel while ignoring an unused high-byte change.

The previous construction runs are excluded from the formal denominator and retained separately. No app save or keyboard/pointer input is permitted. Moving the decoy is the only window-system mutation.

**D — decision**

`PASS_NO_INPUT_STABILITY_GATE_CALIBRATED` only if all 15 captures appear in the exact frozen order; target-only and decoy-moved target frames have identical RGB hashes and zero pairwise RGB changes; each overlapping target frame is 400×180, entirely RGB black and marked `IsViewable`; target/decoy identities are distinct, titles and sizes match, their overlap/move geometries match the schedule; decoy RGB has visible content and differs from black; the cross-stage target changes cover exactly 72,000 pixels and return exactly to baseline; target effect/event files are absent; all processes are reaped; all raw/source hashes independently recompute; and corruption self-controls pass. Otherwise report `HOLD` for unstable/ambiguous evidence, or `STOP` for construction/provenance/infrastructure failure. No retry, replacement, or post-result threshold tuning.

A pass calibrates this XWD visibility/stability gate for this GTK/Xvfb fixture only. It does not prove an application effect, adapter task success, full #3240 reconciliation, or #2606 acceptance.

**C — controls and constraints**

Use the one GTK fixture in `research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py` and the render-only decoy in `research/integration/gtk_effect_control_3240_v1/fixture_render_decoy.py`. Docker image ID, source commit and source hashes are frozen before the fresh formal session. Runtime uses `--network none --read-only`, source mounted read-only and a new evidence directory. Zero model/provider/network/input calls. Keep the earlier #3240 raw bundle unchanged.

**U — unknowns**

Whether this capture behavior transfers to a managed desktop/window manager, another capture API, another toolkit, or another application; whether the earlier adapter's `partial/task_success=null` can be reconciled; whether the full #2606 matrix passes; and whether any user-level benefit follows. This allocation makes no claim on those questions.

## Construction evidence and formal boundary

Construction-only runs (including the initial DISPLAY setup STOP and subsequent runner refinements) live under `evidence/construction*/`. They do not count as formal samples. Formal source, image, order and gates are frozen in `FREEZE.json`; exactly one formal invocation writes `evidence/formal01/`.
