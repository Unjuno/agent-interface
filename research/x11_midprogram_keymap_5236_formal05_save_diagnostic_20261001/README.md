# Issue #5236 formal05 save/effect diagnostic

## H / T / D / C / U

- **H:** formal05's missing saved effects may be caused by a Tk save-event delivery lag after Ctrl-S. A one-second post-dispatch wait tests persistence lag only; passive key events determine whether the fixture saw the save chord.
- **T:** nonformal local Docker diagnostic using Python 3.14 slim, Xvfb, Tk, and the repository's X11 backend/session/fixture. Two fresh US-layout cases use the formal05 click/input/wait/save sequence: exact operations, and exact operations plus one second after dispatch. No layout remap, formal runner, formal allocation, or keymap hypothesis decision.
- **D:** compare dispatch completion, independent effect bytes, and passive Tk key audit immediately after dispatch and after the optional wait.
- **C:** fresh Xvfb and fixture per case; only post-dispatch wait differs.
- **U:** synthetic Docker fixture only; does not establish Arch formal behavior, remapping behavior, WSLg behavior, or a product claim.

## Reproduction

From repository root, with Docker network enabled for Debian packages and Python-Xlib:

```sh
docker run --rm -v "$PWD:/work" -w /work python:3.14-slim-bookworm sh -lc 'apt-get update && apt-get install -y tk xvfb x11-xkb-utils && pip install python-xlib && python -B research/x11_midprogram_keymap_5236_formal05_save_diagnostic_20261001/diagnose.py'
```

No formal allocation is consumed.

## Result

Both nonformal US-layout cases completed all nine operations, verified neutral release, and wrote the exact independent effect `{"saved": true, "text": "a_"}\n` immediately after dispatch. The passive Tk audit recorded `a`, `Shift_L`, `underscore`, `Control_L`, and `s` before either result was sampled. The one-second post-dispatch wait made no difference. Raw stdout-independent records are retained in `results/diagnostic01/raw.json` (SHA-256 `B6D9378096B600DFACC5F4B930030BC91AC740AB6EC1D829AA4AFD69235E4AB3`).

This rejects the narrow hypothesis that the same US-layout operation sequence needs an extra one-second wait to flush the app save. It does not explain the formal05 remap-row STOP; those rows need a fresh, separately frozen successor to examine XKB mapping changes and key-event delivery.
