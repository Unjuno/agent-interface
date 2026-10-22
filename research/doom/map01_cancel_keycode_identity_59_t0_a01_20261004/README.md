# MAP01 cancellation keycode identity T0 A01

## H / T / D / C / U

**H:** The V12 cancellation batch receipt cannot be joined one-to-one to key
admissions when the X server maps distinct admitted key symbols to one X11
keycode, because admission rows retain the symbol but omit the resolved
keycode. The cancellation receipt records intervals by keycode. A normal
injective map should retain one interval per admitted physical keycode; an
alias map should collapse those symbols to one physical interval.

**T:** Execute the frozen V12 candidate source from `FREEZE.json` with a fake
Xlib display and one lease. Compare two admitted keys under (a) an injective
mapping and (b) a mapping where both symbols resolve to the same keycode.
Inspect admission and verified cancellation rows; no native X server or input
backend is loaded.

**D:** PASS for the identity-gap hypothesis if both admissions omit keycode,
the injective control emits two keycode intervals, and the alias case emits one
interval for two symbol admissions. Any other disposition is a construction
failure requiring the result to remain unpromoted.

**C:** Aliased keysyms represent the same physical X key and might reasonably
be treated as one control in some policies. This result does not show that the
MAP01 live keymap aliases W/A, nor that all OS backends need X11 keycodes. It
shows that symbol-level admissions alone do not identify the physical keycode
used by this candidate owner.

**U:** Fake-Xlib construction only. No real X server/keymap, physical input,
game, model, GUI, scorer, recovery, resource allocation, or task effect was
tested. The result does not establish a bug in a live run. A prospective
producer should emit resolved keycode in each admission receipt (or record a
source-bound mapping epoch) before claiming a symbol-to-release join; ordinary
release telemetry also needs that resolved identity to match cancellation
telemetry consistently.

## Executed result

The exact candidate blob in `FREEZE.json` produced two admissions (`W`, `A`)
without `keycode` in both arms. With mapping W→87 and A→65, the verified
cancellation receipt contained two intervals for keycodes 87 and 65. With
mapping W→77 and A→77, the verified cancellation receipt contained one
interval for keycode 77. This confirms the source-level identity gap under the
synthetic alias condition. The retained result is in `RESULT.json`; `audit.py`
independently checks the source pin and expected dispositions without
re-executing the owner.

## Reproduction

From the repository root, with the pinned commit available locally:

```powershell
python research/doom/map01_cancel_keycode_identity_59_t0_a01_20261004/probe.py
python research/doom/map01_cancel_keycode_identity_59_t0_a01_20261004/audit.py
```

The probe loads source by pinned Git commit and verifies its Git blob before
execution. The alias mapping is synthetic; the result must not be reported as
live input qualification.
