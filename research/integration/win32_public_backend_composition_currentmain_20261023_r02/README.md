# Current-main Win32 public-caller synthetic regression R02

This additive packet rechecks the Win32 public MCP caller, owner, cancellation supervisor, and actual `Win32RuntimeSession` / `Win32Backend` composition against current main. `SOURCES.json` binds relevant source files to canonical Git blobs. The test worktree's Git tree matched `origin/main`.

The normal and optimized runs each passed 48 tests. Raw logs, exit codes, and four public-backend event traces per mode are retained here. `conditions.json` records exact commands, runtime, source commit, durations, and trace paths; `audit.py` independently rechecks the retained traces; `SHA256SUMS` covers each packet file except itself.

The tests use synthetic producers and inert Win32 APIs. They cover target-generation changes and unavailable identity, cancellation during the final generation read, confirmed producer retirement before synthetic recovery, independent synthetic readback, UNKNOWN when retirement or observation is unresolved, separate task-effect receipts, and a distinct fresh-generation attempt. They do not qualify native `SendInput`, physical release, live application effect, timing on a real desktop, WSLc, efficiency, or reliability.

The earlier R01 packet remains immutable. This R02 packet refreshes regression evidence after current-main owner/caller source changes; it does not replace any formal experiment outcome.
