# Run commands

Source checkout: current main `6d15df538cff4467a6c72a84a93cfc4557917551`.

1. Start the packet's `source/fixture_app.py` with `--meta <packet>/raw/fixture-meta.json --effect <packet>/raw/effect.json --events <packet>/raw/events.jsonl --effect-delay-ms 6000`.
2. Write `raw/targets.json` as `{"fixture": <fresh hwnd>}` and `raw/window.json` with the fresh hwnd/title and client region.
3. Run `python source/live_probe.py <repo-root> <packet>/raw`.
4. Close only the run-owned fixture with WM_CLOSE, wait for process exit, preserve raw and capture every file hash. Do not replay.
