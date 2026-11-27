# Current-main first-run launcher preflight — three bounded attempts

## Result

R03 is `PASS_LAUNCHER_BOUNDARY` on current main `cfb691b3b890d01c0b24fd1cd988609a62c4dd2a`: 19/19 checks passed in a fresh sparse Git checkout on Ubuntu WSL2 ext4, and the preflight process exited 0. WSL reports `DISPLAY=:0` and `WAYLAND_DISPLAY=wayland-0`; no display was opened. Raw frozen conditions, JSON report, stdout/stderr, and exit code are in `r03-wsl-ext4/`.

R01 ran the same read-only preflight against the Windows-mounted sparse checkout at `/mnt/c`. Its retained JSON is `FAIL_LAUNCHER_BOUNDARY`, 15/19: four committed-byte/LF checks failed for `runtime/golden-demo-v3.sh`, `runtime/golden_desktop_demo_v3.py`, and `runtime/requirements-golden.txt`. The Git source revision was correct; the working-tree files were CRLF/byte-different under the Windows checkout's `core.autocrlf=true`. The report status is authoritative; the separate exit-code capture is empty and is not used.

R02 is retained as an evidence-capture failure. The preflight printed a passing report from a temporary `/tmp` clone, but its wrapper ended with exit 2 because a CR character entered the shell's `exit` argument, and the clone/report were absent on the next WSL invocation. It is excluded from the result; its conditions and post-run custody note are retained in `r02-unretained-wrapper/`. R03 is the clean retained rerun after that capture failure.

## Scope

This result covers only the current-main launcher's committed bytes, modes, syntax, and exact dependency pins. It does not prove full source/package closure, Python dependency installation, `doctor`, retained benchmark reconstruction, GUI operation, model/provider behavior, a fresh golden workflow, or release acceptance. The frozen Research Preview RC1 remains a separate source pin and its supported-host sequence in Issue #58 remains open.

No dependency was installed, no runtime was downloaded, no display or game was launched, no GUI input/model call occurred, and no Docker or formal allocation was used. See `commands.txt` and `SHA256SUMS.json`.
