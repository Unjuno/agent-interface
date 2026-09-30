# Docker diagnostic — fixture focus and saved effect

## H / T / D / C / U

- **H:** the formal runner focused only the Tk top-level window; the fixture's Entry requires a pointer press to acquire widget focus, so key emissions can complete without any app-level key event or saved effect.
- **T:** non-formal, local Docker-only diagnostic. Two fresh Xvfb+fixture cases using Python 3.14 slim, `tk`, `xvfb`, `x11-xkb-utils`, and Python-Xlib. Case A: focus top-level, type `a`, Ctrl-S, release. Case B: same, but move to Entry at client `(50,55)` and left-click before typing. This did not test the XKB mid-wait hypothesis, did not run formal rows, and did not use WSLg or host display.
- **D:** compare dispatch outcome, passive Tk key audit events, and fixture's independent saved-effect file.
- **C:** fresh isolated server/application per case; exact same text and save operations; only Entry click differs.
- **U:** Docker diagnostic only. It establishes neither formal Arch behavior nor any MappingNotify/keymap result.

## Result

Both dispatches reported `completed` and verified release. Without click, `completed_ops=[0,1,2,3]`, `events=null`, `saved_effect=null`. With click, `completed_ops=[0,1,2,3,4,5,6]`, the passive audit recorded the Entry keypress for `a`, Ctrl, and `s`, and the independent effect was `{"saved": true, "text": "a"}`. This supports the missing widget-click hypothesis for the absent effects in formal04; it is a diagnostic inference, not a formal finding.

The diagnostic script is `diagnose.py`; it creates isolated temporary Xvfb servers inside the disposable container and tears them down in `finally`. Reproduce from the repository root with Docker Python 3.14 slim after installing `tk xvfb x11-xkb-utils` and `python-xlib`:

```sh
python -B research/x11_midprogram_keymap_docker_diagnostic_20260930/diagnose.py
```

Formal04 STOP remains immutable at `research/x11_midprogram_keymap_5236_formal04_20260930/results/formal04-20260930-01/`. Any corrected formal run must be a separately frozen successor, with an explicit Entry click and shifted failure-op index.
