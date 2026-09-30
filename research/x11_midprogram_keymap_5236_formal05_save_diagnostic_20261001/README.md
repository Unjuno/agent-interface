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

The remap comparison uses the built image and:

```sh
docker run --rm -v "$PWD:/work" -w /work issue5236-formal05-save-diag:local python -B research/x11_midprogram_keymap_5236_formal05_save_diagnostic_20261001/diagnose_remap.py
```

No formal allocation is consumed.

## Result

Diagnostic 01 compared the exact operation sequence with a one-second host delay after dispatch. Both US-layout cases completed all nine operations, verified neutral release, and wrote `{"saved": true, "text": "a_"}\n` immediately after dispatch. The passive Tk audit recorded `a`, `Shift_L`, `underscore`, `Control_L`, and `s`. The extra second made no difference. Raw: `results/diagnostic01/raw.json`, SHA-256 `B6D9378096B600DFACC5F4B930030BC91AC740AB6EC1D829AA4AFD69235E4AB3`.

Diagnostic 02 directly tested the Issue's proposed `wait_update` after Ctrl-S and before release/teardown. The baseline `Ctrl-S → release` and `Ctrl-S → wait_update(250ms) → release` cases both immediately wrote the same exact effect and recorded the same passive key sequence. The wait completed as operation 8 in the second case; all ten operations completed and release was verified. Raw: `results/diagnostic02/raw.json`, SHA-256 `AEDEF17FE825A0F601A57F58EFFBD25D0A4DC3BC03242990700B9FE91CBA3F31`.

Diagnostic 03 compared the unchanged US row and both mid-wait remap directions in fresh Docker Xvfb/Tk fixtures. All three dispatches completed with verified release; both remap actors exited 0 and final layouts matched their targets. US saved `a_` with events `a, Shift_L, underscore, Control_L, s`; JP→US saved `a` with `a, Shift_L, ??, Control_L, s`; US→JP saved `a=` with `a, Shift_L, equal, Control_L, s`. The independent saved effect therefore differs in both remap rows in this Debian Docker environment. Raw: `results/diagnostic03/raw.json`, SHA-256 `38A546623D6CFB0B2628663F4E6D94E6A65901E37934AAB4B35C94867D72B22B`.

The US controls reject a simple missing post-save wait. Diagnostic 03 supports the remap/key-interpretation hypothesis in Docker, but its Debian image and XKB data are not the Arch formal environment. Formal05's passive audit shows `a`, `Shift_L`, and the post-remap character (`??` or `equal`) but no `Control_L` or `s`, whereas these Docker rows do receive the save chord. Thus the Docker remap findings corroborate wrong mapped text, but do not explain formal05's missing save events or missing effect. That difference needs source/environment-level investigation and a separately frozen Arch successor; formal05 remains STOP and must not be rerun.
