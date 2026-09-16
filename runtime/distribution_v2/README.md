# Portable unified runtime zipapp v1

This package builds one deterministic `agent-interface-runtime.pyz` containing the promoted execution modules only:

- `runtime/core_v1`;
- `runtime/selector_v1`;
- `runtime/cli_v1`;
- X11, Win32 and Quartz promoted backend/session modules.

The archive contains no tests, fixtures, research tree or retained evidence. It is built from exact committed Git blob bytes with fixed ZIP timestamps/mode/order, so Windows checkout newline conversion cannot change the artifact.

Usage:

```bash
python agent-interface-runtime.pyz doctor
python agent-interface-runtime.pyz dispatch \
  --program program.json \
  --targets targets.json \
  --current-observation-seq 7 \
  --current-binding-revision 3
```

Requirements:
- Python 3.12+;
- Linux/X11: `python-xlib` plus a usable `DISPLAY`;
- Windows: promoted Win32 backend, explicit HWND targets;
- macOS: promoted Quartz backend, explicit PID targets, Accessibility + Screen Recording permissions;
- Wayland-only Linux: not promoted and fails closed.

The archive does not discover targets or request permissions automatically.
