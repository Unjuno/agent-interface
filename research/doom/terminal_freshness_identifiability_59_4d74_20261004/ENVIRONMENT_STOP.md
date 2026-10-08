# Separate neutral ViZDoom probe preflight — STOP

The proposed `TERMINAL-EPOCH-59-4D74-20261004-01` neutral CPU integration probe was not started. Current host checks found:

- `wslc.exe` is unavailable.
- Python is 3.12.13 and `import vizdoom` raises `ModuleNotFoundError`.
- OrbStack Docker is reachable (`29.4.0`, 10 CPUs, 16,808,173,568 bytes reported container memory), but the exact pinned image `sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378` is absent (`docker image inspect`: `No such image`). A prior image inventory read also failed on a containerd content blob with `operation not supported`.
- No `freedoom2.wad` or `basic.wad` was found under the active Codex workspace.

No image or package was downloaded, built, or installed; no game process, GUI, model, or input was started. This is an environment preflight STOP for that one-shot probe, not a ViZDoom result and not a fleet-wide availability claim. The independent source-level identifiability experiment in this package is a distinct low-resource test of the same freshness question.
