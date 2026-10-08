# Corrected Xdummy native XKB map round-trip — retained result

Task `XKB-XDUMMY-MAP-ROUNDTRIP-20260916-002`, Issue #387. Publication BASE `a890afb391ad1aa99b29bb45493fa4d11c0da79c`; source-first freeze HEAD `d8dee6b387f36225086ba05099741c97839d38cc`.

## Decision

**`PASS_XDUMMY_NATIVE_XKB_MAP_SCOPED`.**

After repairing only the predecessor harness's per-process DISPLAY/XAUTHORITY propagation and typed failure finalization, three fresh Xdummy/Xorg servers all loaded the same frozen German XKB map and exposed the requested native readback state. This is a server-environment result; it does not by itself prove native application text delivery.

## Formal block

Exactly three fresh authenticated Xdummy/Xorg servers on :180/:181/:182. Zero XTEST, Tk, key, task or model operations. Every arm independently resolved German XKB SHA-256 `3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd`, verified resolved AD01 `[q,Q,at,Greek_OMEGA]` and RALT `ISO_Level3_Shift`, captured baseline full-server/core/modifier state, loaded the full map through `xkbcomp -w 0`, and repeated the readbacks.

All three arms are byte-for-value identical on decision-relevant identities:

- Xdummy startup: 3/3;
- XKEYBOARD extension present: 3/3;
- native load return code: 0, 3/3;
- resolved SHA: exact, 3/3;
- baseline server dump SHA: `0e0746bf5f507ac5d73d7614f65d4c1c6bafcebf64edff570957cc2ddc0a75e5`;
- after server dump SHA: `e7dffba4c93fa1972fd4ba875fd6221e0ec37ad6e5e69be43385889163326bc1`;
- baseline core+modifier SHA: `2f5250d40d3070d9307d61bf0568946bce3f0eba96c4ed9b8bd03d8ff1a40966`;
- after core+modifier SHA: `56287bd0bd0ee5cf0daa8100cb8f274e9ea5c3860496a4091aa7e70feae0f2ff`;
- readback AD01 symbols: `[q,Q,at,Greek_OMEGA]`, 3/3;
- readback RALT: `ISO_Level3_Shift`, 3/3;
- input operations: 0.

Frozen independent audit returns `PASS_INDEPENDENT_AUDIT`, decision `PASS_XDUMMY_NATIVE_XKB_MAP_SCOPED`, 3/3 arms. Five post-formal retained-byte corruptions are rejected: resolved-hash receipt, server-dump bytes, summary decision, input count and arm decision. Formal was not rerun.

## Predecessor and comparison boundary

Consumed #380 remains `HARNESS_FAIL_AUTH_ENV` and is not pooled. Its source bug was exactly the missing runner-process DISPLAY/XAUTHORITY propagation; the successor additionally guarantees typed `HARNESS_FAIL` finalization. Xdummy invocation, German map, displays, arm count, no-input contract and map/readback gates are otherwise unchanged.

Separately, merged #372 used the same German resolved XKB and native load command on fresh Xvfb servers. There, load returned0 but server/core state remained byte-identical US in 3/3 arms. Here Xdummy/Xorg changes both readback surfaces consistently. This supports an environment-specific X-server boundary; it does not prove every Xorg desktop behaves like Xdummy or that Xvfb can never be configured differently.

## Evidence

Conversation archive `xkb_xdummy_map_roundtrip_v2_evidence.tar.xz`: 16,872 bytes, SHA-256 `8625c8c64b3df33b1650f03dea11acd6d3a8cc9f303e11c59b562066115c0a94`; manifest SHA-256 `61958e18323f90baf13d2f0c07cc786c9dc0289be5528b80e45a406fafdab603`; 40 files including manifest. GitHub retains exact source/freeze plus compact result/audit/mutation/artifact metadata.

## Limits / next question

Xdummy is an LD_PRELOAD wrapper around Xorg with the dummy video driver, not a physical interactive desktop. This result proves only that this reproducible server class accepts and exposes the frozen native XKB state. It does not test XTEST text delivery, application interpretation, physical keyboard state, dead-key/Compose, Wayland, Windows/macOS, or performance.

The next one-variable rung is now authorized: keep this exact Xdummy/XKB environment and whole-payload preflight, and compare the eight direct German level-3 printable symbols plus dead-key negative controls using **native XKB state/types rather than the projected core-map/Mode_switch fixture**. Do not add Compose in the same rung.
