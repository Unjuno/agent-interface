# R03 execution

1. Started a fresh fixture and recorded `raw/fixture-command.json`, metadata, HWND/PID and window geometry.
2. Used Computer Use Raise on the unique run-owned fixture and saved `raw/foreground-before-action.json`.
3. Ran `python source/live_probe.py <patched-checkout-root> <packet>/raw` once.
4. Preserved one MCP dispatch. Do not replay.
5. Closed the exact fixture with Computer Use Alt+F4 after public session close.
