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


For an explicit X11 target, capture once and present that retained image:

```sh
python agent-interface-runtime.pyz observe --targets targets.json --target fixture \
  --frame window_client --region 0 0 400 180 --capture-directory images > observation.json
python agent-interface-runtime.pyz review --report observation.json --run-directory . > review.json
```

`targets.json` maps the caller's target name to its X11 window ID. Select the
intended display with `--display` on observe when necessary. PNG capture requires
Pillow in addition to python-xlib. Review needs only the Python standard library
and does not connect to a display. Its image block contains base64 PNG data for
the host to forward as an image input; do not paste it as model-visible text.
Check both the retained receipt status and image_status: successful image
presentation does not mean the application task or cleanup succeeded.

On WSL, filesystem and abstract X11 sockets may coexist. For owned Xvfb tests,
verify the display is unused before launch and verify the connected screen;
do not assume automatic display-number allocation identifies the intended server.
The actual zipapp route is recorded in runtime/results/public-portable-review-01.
