# Native XKB map round-trip before native AltGr delivery — retained setup boundary

Task `XKB-NATIVE-MAP-ROUNDTRIP-20260916-001`, Issue #372. Publication BASE `5a5b748c554fd5e28958a70c750d7fe3dafc65d3`; source-first freeze HEAD `1b5d592e72464d91f2e8c8b4cf0511b490a645fa`.

## Decision

**`SETUP_BLOCKED_NATIVE_XKB_APPLY`.**

The container's Xvfb server advertises the XKEYBOARD extension and the installed XKB toolchain can resolve the standard German layout exactly, but loading that fully resolved keymap into the live Xvfb server returns success without changing any of the three frozen readback surfaces. Native AltGr delivery is therefore not allocated in this environment. The previous projected-core-map result (#360 / PR #365) remains scoped evidence; it is not silently promoted to native XKB semantics.

## Frozen formal block

Three fresh authenticated `xvfb-run` servers, zero XTEST/Tk/key/task input. Every arm:

1. records XKEYBOARD extension presence, `setxkbmap -query`, python-xlib core/modifier map, and full `xkbcomp -xkb $DISPLAY -` server dump;
2. resolves `de` using `setxkbmap -layout de -print` + `xkbcomp -xkb`, requiring SHA-256 `3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd`;
3. verifies the resolved map contains `<AD01> = [ q, Q, at, Greek_OMEGA ]` and `<RALT> = ISO_Level3_Shift`;
4. loads the full resolved map with `xkbcomp -w 0 de.resolved.xkb $DISPLAY`;
5. repeats the three live readbacks.

No `XChangeKeyboardMapping`, Mode_switch fixture projection, XTEST, receiver or payload delivery is allowed.

## First outcome

All three arms agree exactly:

- XKEYBOARD extension: present;
- resolved German XKB hash: exact preregistered value;
- `xkbcomp` server-load return code: `0`;
- load stderr/stdout: empty;
- baseline query: `layout: us`;
- after query: still `layout: us`;
- full server XKB SHA-256 before/after: `0e0746bf5f507ac5d73d7614f65d4c1c6bafcebf64edff570957cc2ddc0a75e5` / identical;
- live core+modifier mapping SHA-256 before/after: `2f5250d40d3070d9307d61bf0568946bce3f0eba96c4ed9b8bd03d8ff1a40966` / identical;
- live `<AD01>` keycode 24 row remains `[113,81,113,81,0,0,0]` (`q,Q,q,Q,...`), so level3 `@` is absent;
- modifier mapping before/after is identical;
- input operations: `0`.

Thus the loader's exit status cannot be treated as proof that the live server adopted the requested XKB state in this environment.

## Audit / negative controls

The frozen auditor imports no runner code. It re-hashes the retained resolved/server dumps, reparses German `<AD01>` and `<RALT>`, recomputes changed/unchanged server state, verifies zero input, and re-derives PASS/BLOCK/FAIL. Result: `PASS_INDEPENDENT_AUDIT`, decision `SETUP_BLOCKED_NATIVE_XKB_APPLY`, 3/3 arms.

A separate post-formal retained-byte mutation check rejects 5/5 corruptions: resolved-hash receipt, server dump byte, summary decision, input-operation count, and arm decision. Formal measurement was not rerun.

## Construction chronology

Excluded construction is retained rather than pooled. The first attempt failed because `xmodmap` is absent. Subsequent input-free construction checked `setxkbmap -layout de`, `setxkbmap -print` piped to server `xkbcomp`, and a fully resolved XKB file loaded by `xkbcomp`; all returned success/no error while live state remained US. One excluded runner harness check returned the same BLOCK disposition. These observations were preregistered before the three formal arms.

## Evidence boundary

Conversation archive `xkb_native_map_roundtrip_v1_evidence.tar.xz`: 19,040 bytes, SHA-256 `ee7856515484ceb487f6d9d35cde0a361558afca9afdb4ceb8ce362d224a0427`; evidence manifest SHA-256 `adc0977cb1464239bf1359a97818fc85cd1d5ba7768001ecc7d3fcda5439cbba`; 95 regular files including the manifest. GitHub retains exact source/freeze plus compact result/audit and artifact metadata.

## Limits / next question

This result is specific to Linux/Xvfb with `setxkbmap 1.3.4`, `xkbcomp 1.4.7`, python-xlib 0.15, CPython 3.13.5 and kernel 6.18.44. It does not show that normal Xorg, nested X servers, Wayland/Xwayland, or physical desktops have the same loading behavior. Core-map readback also does not by itself represent all XKB type/state semantics.

The next one-variable discriminator should change the X server environment, not the text mechanism: if an available standard nested/desktop X server can accept the same resolved German XKB and expose it on readback, then native AltGr delivery can be tested there. If no such server is available in the reproducible container, retain the native-XKB path as environment-blocked rather than reintroducing the projection under a new name.
