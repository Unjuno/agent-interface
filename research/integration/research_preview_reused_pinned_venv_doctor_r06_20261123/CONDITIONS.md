# Existing pinned venv current-main doctor R06

- Attempt: RP-CURRENT-MAIN-REUSED-VENV-DOCTOR-R06-20261123-01
- Frozen source: 7e9caab2acf8428beeb48682edd5e7a0bace4967 (main after PR #10490)
- Host: Ubuntu WSL2/WSLg, ext4; Python 3.12.3 in the preserved R05 RC1 venv.
- The preserved venv was explicitly installed in R05. Its nine installed distributions match this current-main requirements file byte-for-byte (SHA-256 1065afbce7e148dfb1a736cba251b81620898adc274761e411262ca4742341d3). No packages were installed or changed in this attempt.
- Frozen command: invoke runtime/golden_desktop_demo_v3.py doctor using /home/user/agent-interface-rp-rc1-doctor-r05-20261121/runtime/.venv/bin/python; set only AGENT_INTERFACE_CHROMIUM to /mnt/c/Program Files/Google/Chrome/Application/chrome.exe.
- This doctor performs path/import/X11-connect checks and only invokes Windows Codex CLI --version when its configured JS entrypoint exists. The precheck found no configured CLI JS entrypoint, so that subprocess path was not entered.
- No dependency installation, model/provider call, GUI launch/input, Docker/WSLc, or live allocation.
