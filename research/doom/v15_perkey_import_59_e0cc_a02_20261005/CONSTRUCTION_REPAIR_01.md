# Construction repair 01 — optional workbook import stub

The first frozen route attempt (`results/current-head-4158-run01/`) stopped
before the `suite.Session` boundary because the host Python does not have
`openpyxl`. The exact import chain and `ModuleNotFoundError` are retained in
the run's stderr; its outcome remains `STOP_ENVIRONMENT_IMPORT`, not a feature
result.

Static inspection of the frozen `gui_suite.py` source shows the imported
`Workbook` and `load_workbook` call sites are inside later application-task
functions (lines 310 and 407 in that frozen file). The startup identity probe
must stop before those functions run. Repair 01 therefore installs inert
callables for only those optional names; either callable raises the existing
forbidden-operation exception if invoked. It does not alter V12, V15, the
bridge, release owners, or the owner-selection decision.

The repaired probe and replay wrapper are separately frozen as
`probe_startup_v2.py` and `replay_startup_v2.py`. Attempt 02 uses a fresh output
directory. The failed first attempt remains byte-for-byte retained.
