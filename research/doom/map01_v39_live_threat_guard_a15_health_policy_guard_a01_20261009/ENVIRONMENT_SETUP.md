# A15 environment and launch contract

Host: local Mac. Game lane: dedicated OrbStack VM `issue59-live-v39-a01-20261009`, currently running with only normal system services and no game, Xvfb, controller, or app-server process. Its `/mnt/source` mount points at the parent project directory; the repository maps to `/mnt/source/results-local/doom/a14-source`.

Guest preflight requires Python 3.12.3, ViZDoom 1.3.0, Pillow 12.3.0, python-xlib 0.33, openpyxl 3.1.5, the qualified Freedoom WAD SHA-256, Xvfb 1280x800, at least 2 GiB available memory and `/tmp`, and no existing game/display process. Recheck all conditions against the exact A15 branch before launch.

The host relays the installed Codex CLI app-server over stdio with plugins and shell tools disabled. The bounded JSONL relay verifies local-image bytes against guest custody receipts before forwarding. The guest uses only the frozen A15 source tree. Episode cap is 600 seconds; host relay cap is 900 seconds. No retry or automatic resume. Do not stop the OrbStack VM after the run; only confirm child game/display/controller processes are gone and record the lane release.
