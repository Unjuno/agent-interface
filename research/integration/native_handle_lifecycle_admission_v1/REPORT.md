# Native-handle lifecycle admission boundary — Issue #4197

**Scoped scientific result: `PASS_LIFECYCLE_BOUND_NATIVE_ADMISSION_SCOPED`.**

This is an additive research admission-wrapper experiment. It does **not** modify or execute the canonical `NativeHandleBridge` internals and is not a production/runtime promotion. It tests the missing composition condition exposed jointly by #3950/#3974 and #3575: a same-process window can be destroyed and recreated with the same XID, geometry and pixels, so process/server incarnation alone is insufficient; an observer-derived window lifecycle token can fail closed before the native-input boundary.

## H/T/D/C/U

- **H:** binding an alias to the observed window lifecycle rejects stale same-XID replacement aliases before input while allowing current aliases; an observer restart yields UNKNOWN/refusal.
- **T:** one prospectively frozen formal invocation, four fresh private Xvfb/client sessions × three cases = 12 rows: SAME_LIFETIME, RECREATED_SAME_XID, OBSERVER_RESTART. Same actor/tracker mechanism as final excluded construction. No formal retry/replacement/tuning.
- **D:** 12/12 exact. Same-lifetime 4/4 allowed and produced exactly one independently observed ButtonPress effect with three XTEST emissions. Recreated stale aliases 4/4 reused the exact XID and exact pixel hash but had different lifecycle tokens, refused before the boundary, emissions 0, effect delta 0. Observer restart 4/4 had no current lifecycle token, refused UNKNOWN, emissions/effect 0. Terminal keymaps/buttons neutral, actor/Xvfb exits 0 and sockets removed in all sessions. Independent raw-only audit errors=[]; supplemental corruption controls reject 10/10 mutations.
- **C:** synthetic local X11 wrapper and root SubstructureNotify coverage only. This does not establish production observer coverage, reparenting/gap semantics, atomic check/use, arbitrary toolkit behavior, public CLI acceptance, model utility or performance.
- **U:** actual NativeHandleBridge/public-path composition, reconnect/gap transport and end-to-end #2789/#3311 evaluation remain open.

## Preserved construction and audit failures

Excluded construction retained four setup failures before the final pass: import-path isolation, absent Xauthority path, Xlib warning framing on stdout, and incorrect resource-ID reuse index. None is pooled into formal evidence.

The formal invocation itself exited 0 and wrote all 12 rows. The independent raw audit exited 0. The **first corruption-control command** used `python -I controls.py` and stopped because isolated mode removed sibling `audit.py` from the import path. No formal/raw/source byte was changed or rerun. The exact frozen `controls.py` was then executed read-only under normal Python import rules; it rejected all 10 mutations. This supplemental control PASS does not erase the first postformal control-launch STOP.

## Exact provenance

- intake/current source main: `b805dabeb5c3bc66fc7bd4d35e7c731bb116dbef`
- canonical bridge reference blob: `aa72a835a60ab9bf9f053c680a1a3d81e49c14d5`
- #3974 lifecycle candidate reference blob: `37ee3068f3614d22acdb68582f0a98ae5bd415f4`
- #881 typed predecessor blob: `91983ab78a06b93cc7fdd829b6094fd255f18210`
- preformal FREEZE SHA-256: `f8ec1d8be7b97b04cdf197fd517699f6aabf6b77cda3d9fc9ba62d584b70b55a`
- raw SHA-256: `b67790414851ebbe0ed82cb835eefc03b884ac89190d6d39040f004b416dd193` (12,593 bytes)
- formal invocations: 1; formal retries/replacements: 0
- environment: provided Linux x86_64 execution container, CPython 3.13.5, Python-Xlib 0.15, Pillow 12.3.0, private Xvfb `-nolisten tcp -ac`; Docker/Podman unavailable, no image-attested Docker/OrbStack claim.

## Integration handoff

This result strengthens the #2789 source/target-identity seam at the design-requirement level: **process/server incarnation and exact current pixels are not enough; a window-lifecycle generation must be current, and unavailable lifecycle coverage must fail closed.** It does not itself implement that requirement in the canonical bridge or public runtime.
