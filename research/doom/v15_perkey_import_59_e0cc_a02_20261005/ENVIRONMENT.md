# Construction environment and preserved WSLc preflight

This is an ordinary mocked startup-selection construction, not a live/formal
allocation. `wslc.exe list` showed no running containers. WSLc reported that
the host kernel lacks swap-limit cgroup support.

The first WSLc preflight command included unsupported `--read-only`; WSLc
rejected the option before starting a container. After removing that option,
the pinned cached image `python@sha256:1ae5b32b33f502335ed9f5ee7afa4387192e9566b1328fc66da836c77c1cfb65`
started with networking disabled and failed the dependency check at
`ModuleNotFoundError: No module named 'PIL'`. The image is Python 3.14.8. No
candidate route was run in WSLc.

For the candidate, use the installed Windows Python 3.11.9 environment, which
has Pillow 10.4.0 and NumPy 2.4.6 required by the import closure. The probe
replaces VizDoom/Xlib bindings with inert stubs, replaces the session
constructor with an exception boundary, and refuses subprocess and thread
creation. It does not start a game, GUI, X server, owner thread, model, or
native input. This host fallback is a startup identity check only; it does not
claim the missing WSLc resource controls were enforced.
