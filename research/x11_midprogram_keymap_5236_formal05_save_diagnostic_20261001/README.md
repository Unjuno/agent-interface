# Issue #5236 formal05 save/effect diagnostic

## H / T / D / C / U

- **H:** formal05's missing independent saved effects may be due to application-side event/save delivery lag after Ctrl-S, or due to the changed XKB map causing the Ctrl-S chord to produce a different event. A post-dispatch wait tests only persistence lag; event logs distinguish whether the fixture observed the expected key events.
- **T:** nonformal local Docker diagnostic on Python 3.14 slim, Xvfb, Tk, and the exact repository X11 backend/session/fixture sources. Three fresh US-layout cases use the formal05 click/input sequence: (1) exact operation sequence; (2) same sequence plus one second of host time after dispatch; (3) reserved for a future isolated fixture callback comparison. No layout remap, no formal runner, no formal allocation, and no hypothesis decision.
- **D:** compare completed operations, passive Tk key audit, and independent effect bytes immediately after dispatch and after the optional wait. This diagnostic does not classify formal H.
- **C:** one fresh Xvfb and fixture per case; same base task sequence; only post-dispatch wait differs in the second case.
- **U:** synthetic Docker fixture only; no Arch formal environment, XKB remap timing, WSLg, user app, or production claim.

The third case is intentionally not executed pending a valid non-invasive way to request a fixture save; do not interpret it as data.

## Reproduction

From repository root:

```sh
docker run --rm --network none -v "$PWD:/work" -w /work python:3.14-slim-bookworm sh -lc 'apt-get update && apt-get install -y tk xvfb x11-xkb-utils && pip install python-xlib && python -B research/x11_midprogram_keymap_5236_formal05_save_diagnostic_20261001/diagnose.py'
```

No formal allocation is consumed by this diagnostic.
