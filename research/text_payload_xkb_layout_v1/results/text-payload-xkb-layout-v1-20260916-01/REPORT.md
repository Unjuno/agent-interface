# XKB layout transfer v1 — retained formal failure

**Result ID:** `text-payload-xkb-layout-v1-20260916-01`  
**Source/plan freeze:** `aecfd1d1ddddaa9d87ec56900a24b10b9b2f19a7`

## Disposition

**FAIL_FORMAL_FIXTURE_RESTORATION_GATE**. This result executed once and was never rerun.

All 380 character-level gates passed: accepted characters were exact; rejected characters injected zero input and produced no application text; applied map remained unchanged during candidate delivery; release was verified. However, every arm failed the frozen in-server exact map-restoration gate. The aggregate therefore remains FAIL.

Observed coverage: US 95 accepted / 0 rejected; German 85 / 10; French 85 / 10; US Dvorak 95 / 0. These observations do not override the formal failure.

A post-result diagnostic, not part of the formal allocation, found that the fixture's `XChangeKeyboardMapping` projection/restoration path changed Xvfb core-map normalization: the original map was 7 keysyms/keycode and restoration normalized to 15, so byte-exact restoration was unavailable through this fixture mechanism. This diagnosis motivated a separately allocated process-isolation successor; it does not repair or relabel this first outcome.
