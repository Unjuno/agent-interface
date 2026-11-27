# R02 execution

1. Start `source/fixture_app.py` with fresh `--meta`, `--effect`, `--events`, and `--effect-delay-ms 6000` paths.
2. Record fresh HWND, PID, process creation identity, window rect and foreground evidence.
3. Run `python source/live_probe.py <patched-checkout-root> <packet>/raw` exactly once.
4. Preserve the public raw response, producer packet, event/effect files and late-input evidence.
5. Close only this fixture after terminal custody is resolved. Never replay the action.
