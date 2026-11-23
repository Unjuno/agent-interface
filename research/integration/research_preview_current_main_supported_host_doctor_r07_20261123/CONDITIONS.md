# Research Preview supported-host doctor R07

- Date: 2026-11-23 UTC.
- Purpose: recheck the current WSL/WSLg host's non-live Research Preview prerequisites after PR #10522.
- Runtime/RC source comparison: `runtime/` and `release/preview_bundle_v1/` are unchanged between `8554b2bf` (the R06 doctor evidence base) and current main `095d92b1696e03c266287b530cbb38f5b9d5e7f6`.
- Doctor source: the retained R06 current-main checkout at `/home/user/agent-interface-preview-main-r06-20261123/runtime/golden_desktop_demo_v3.py` (frozen source `7e9caab`, after PR #10490).
- Python: preserved R05 WSL venv `/home/user/agent-interface-rp-rc1-doctor-r05-20261121/runtime/.venv/bin/python`, Python 3.12.3. This environment was already present; no package was installed or changed. R06 previously recorded that its nine installed distributions exactly match the requirements hash `1065afbce7e148dfb1a736cba251b81620898adc274761e411262ca4742341d3`.
- Chromium override: `/mnt/c/Program Files/Google/Chrome/Application/chrome.exe` (`AGENT_INTERFACE_CHROMIUM`). The doctor checks the configured path; it does not launch Chromium.
- Expected Windows CLI entrypoint: `%APPDATA%/npm/node_modules/@openai/codex/bin/codex.js`; it was absent on both Windows and the WSL-mounted path at execution time. `codex` resolving to the Windows desktop application is not substituted for this JavaScript CLI entrypoint.
- Invocation: `wsl.exe -d Ubuntu -- env AGENT_INTERFACE_CHROMIUM='/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' /home/user/agent-interface-rp-rc1-doctor-r05-20261121/runtime/.venv/bin/python /home/user/agent-interface-preview-main-r06-20261123/runtime/golden_desktop_demo_v3.py doctor`.
- No installs, downloads, Docker/WSLc operations, model/provider calls, Chromium launch, GUI input, fresh Golden task, or `audit-live` occurred.
- Stopping rule: doctor must pass all 15 checks before fresh no-retry acceptance. Since `windows_cli` and dependent `codex_cli` failed, no live acceptance task was started.
