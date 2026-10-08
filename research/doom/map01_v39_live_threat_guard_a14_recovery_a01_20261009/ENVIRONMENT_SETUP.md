# A14 environment and launch contract

Host: local macOS; dedicated OrbStack VM `issue59-live-v39-a01-20261009`, already running. The VM mounts the parent repository read/write at `/mnt/source`; frozen A14 source root is `results-local/doom/a14-source`. Runtime is an isolated VM, not a Docker container.

Guest preflight requires Python 3.12.3, ViZDoom 1.3.0, Pillow 12.3.0, python-xlib 0.33, openpyxl 3.1.5, the qualified Freedoom WAD SHA-256, 1280x800 Xvfb, at least 2 GiB available memory and `/tmp`, and no existing ViZDoom/Xvfb/game process.

The host launches the installed Codex CLI app-server over stdio with plugins and shell tools disabled. A bounded JSONL relay verifies local-image bytes against guest custody receipts before forwarding. No provider-side decoded-byte receipt is claimed. The guest uses only the frozen source tree. The game episode is capped at 600 seconds and the host relay at 900 seconds. There is no retry or automatic resume.
