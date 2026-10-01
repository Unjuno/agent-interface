# Native XKB German server-state round-trip — retained result

Task `XKB-NATIVE-DE-ROUNDTRIP-20260916-001`, Issue #412. Base `f224cc42c083c9139185e3f89800fcd21bbea0a4`; source-first freeze `61f2e22dc095389cb718867e10ce06b4923da90a`.

## Decision

**`PASS_NATIVE_XKB_ROUNDTRIP_PREREQ`**.

Three fresh private Xvfb servers all advertised XKEYBOARD. On every server, the single frozen command `setxkbmap -layout de` returned 0. The post-command server XKB dump changed from the common baseline SHA-256 `0e0746bf5f507ac5d73d7614f65d4c1c6bafcebf64edff570957cc2ddc0a75e5` to `3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd`. That after-state is byte-identical to the independently resolved installed German definition, SHA-256 `3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd`.

All three cases also changed both client-visible core keyboard mapping and modifier mapping. The frozen independent auditor reparsed the post-server XKB and found all required direct level3 symbols (`@ [ ] \\ { } | ~`) in 3/3 cases. Formal audit: `PASS_AUDIT`; direct-after 3/3; observable-change 3/3. No XTEST, key/button event, receiver, application task, model or game call occurred.

This corrects the earlier exploratory suspicion that fresh Xvfb might not apply the standard German XKB layout. Under the frozen command/toolchain in this allocation, the round-trip is exact and reproducible across all three fresh servers. That earlier exploratory observation was not formal evidence and is not retained as a contradiction.

## Integrity

GitHub source readback preceded formal execution. A comment-only transcription difference in `run_case.py` was detected before formal; the execution checkout was changed to the already-frozen GitHub bytes, then blob identity was rechecked. No formal case had run before this correction.

The frozen auditor establishes the preregistered decision. After formal completion, a stricter posthoc verifier cross-checked report↔results equality, all retained server/XKB SHA-256 values, keyboard/modifier fingerprints, changed booleans, and exact after-server == resolved-German bytes. It passes 3/3. Four retained-byte corruption controls are rejected. This strict verifier is posthoc supporting evidence, not a replacement preregistered gate.

## Limits / next rung

This is a server-state prerequisite only. It does **not** test actual native level3 text delivery, XKB type/group state during key events, dead-key composition, IME, physical keyboards, Wayland, Windows/macOS, latency or product reliability. The next single-factor experiment may now test the same eight direct German level3 symbols through the native server XKB mapping **without manual core-map projection**, preserving whole-payload preflight and zero-input rejection for dead-key-only payloads.
