# R05 host prerequisite probe follow-up

This read-only probe was frozen after the R05 doctor result to preserve the exact search scope behind the environment diagnosis. It is not a new RC1 setup attempt and changes no host state.

- Probe ID: `RP-RC1-R05-HOST-PROBE-20261121-01`
- Current main at probe: `64e5a041789d421f3ef1db2c0e4b66b94de14238`
- Target release source: `8e5052e04f8720fe89052ad01127114dd6852d88`
- Result: Windows Codex `codex.js` was absent from the five recorded candidate install roots; Windows Chrome exists at `C:\Program Files\Google\Chrome\Application\chrome.exe`; no WSL Chromium command or matching dpkg package was listed.
- Scope limitation: absence is asserted only within the paths/commands listed in `conditions.json` and `raw/host_probe.ps1`.
- No install, launch, GUI action, model call, formal allocation, or Docker/WSLc action occurred.

`raw/stdout.txt`, `raw/stderr.txt`, and `raw/exit-code.txt` are the captured process streams/status. `SHA256SUMS` covers the frozen conditions and raw files including the exact probe script.
