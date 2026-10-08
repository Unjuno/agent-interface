# Current-main source comparison (2026-10-07)

Read-only comparison against `origin/main` at
`9fb2dd6782d1d1477a00d14be870487fd4c54fa2` found 8 of the 11 frozen
`research/live_control/` sources byte-identical to the 2026-10-04 freeze.
Three paths have advanced on current main:

- `research/live_control/executor_v12.py`
- `research/live_control/input_owner_v12.py`
- `research/live_control/input_transition_owner_v4.py`

This is source drift, not a failure of the historical fake-Xlib run. Its
frozen source copies, `PRE-RUN.json`, `RAW-30.json`, `AUDIT.json`, `RUN.json`,
and original checksum manifest remain byte-for-byte intact and are checked by
`verify_preserved_hold_bound_30.py`. No candidate or auditor was rerun, and no
current-main runtime/effect qualification is claimed.
