# Excluded pre-dispatch setup attempt

2026-11-22T09:35:16Z: Foreground probe was invoked with a PowerShell variable named `$pid`; PowerShell resolved its read-only host PID (30888) instead of fixture PID 36288. Probe correctly returned `foreground_matches=false`. No MCP observation or input dispatch occurred. The attempt is excluded; correct variable naming and rerun identity check before any input.

2026-11-22T09:35:40Z: Runner setup stopped before its first MCP call because `raw/window.json` had not been materialized. No observation or input dispatch occurred. Added the observed CUA screenshot dimensions and fixture identity to `window.json`; recheck foreground before launching the runner.

The first attempt to save final test logs used packet-relative paths while the shell was inside the test module directory; the shell returned path-not-found before either test command started. The tests were then run from the module directory with absolute packet output paths.
