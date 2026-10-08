# Execution notes — Allocation 06

The frozen GitHub commit was cloned at branch head and every preregistered source/plan SHA-256 matched FREEZE.json before execution. The authoritative exact-byte run is RUN_BYTE_IDENTICAL.json; it used Python 3.14.5 with -B and the frozen runner/source files, without altering line endings. The distinct follow-up process ran audit_independent.py on that exact raw JSON and returned errors=[]; see AUDIT_BYTE_IDENTICAL.json.

An earlier exploratory execution copy had normalized mixed LF/CRLF endings and is retained unchanged as RUN.json/AUDIT.json. It is not the confirmatory run. The earlier hash mismatch and fixture-reference error are retained in PREFREEZE_NOTES.md; neither was overwritten.

Exact-byte result: 14/14 owner tests pass; candidate accepts pristine inventory and rejects all seven preregistered deletion/corruption controls; baseline auditor false-accepts omission controls; v10/v11 request sequence and XSync count match (7 each), with empty final fake key state and three verified-neutral terminal records.

Scope remains deterministic host fake-Xlib construction only. No Docker/shared lease, real X11, GUI, physical input, game, model, GPU, live held-input occupancy, or MAP01 task efficacy was tested. This is not formal X11 allocation evidence.
