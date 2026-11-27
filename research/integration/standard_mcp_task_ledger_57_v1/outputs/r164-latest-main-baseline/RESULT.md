# Issue #57 Calc public composition — current-main verification

- Source is frozen at current `origin/main` `3b941f8963a2c7ab739aec9c0d76740cb44cb6ec`.
- Windows CPython 3.11.9 focused provider/Fake X/public-MCP composition passes 1/1 normally (25.043 s) and 1/1 under `-O` (23.778 s).
- Raw stdout/stderr, exact selector, source SHA-256, exit and raw hashes are retained beside this report.
- This verifies a synthetic composition fixture only. It does not establish external provider usage, live GUI or MAP01 task success, recovery reliability, or matched efficiency. Issue #57 remains open.

An earlier checkout at `897f4896` failed the same selector after a candidate had switched the owner factory but omitted `calc-task-values.json` in the parent temporary root. A one-line diagnostic patch made that stale checkout pass in both modes. The latest-main baseline passes without that patch, so the stale-checkout failure is not an outstanding current-main defect and no patch is proposed from it.
