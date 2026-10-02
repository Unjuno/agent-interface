# First primary modal-tools Calc allocation: setup stop

Disposition: HOLD_SETUP_WINDOW_DISCOVERY. Source f058743de58cdd23ec82128af392b08ce8c65739;
scaffold frozen at 14ecb225e before launch. Original owner handle 49798 exited 1.
Seed 1001076; no fixture/input retry and no replacement of this allocation.
The keeper timed out after 30s using legacy WM_NAME to locate the workbook window.
No window-inventory diagnostic was captured, so the reason is NOT independently
established. Prior Calc evidence documents missing legacy titles; this suggests
an engineering correction, not proof of this allocation's exact failure cause.

primary_stdio was never launched. No public requests, model image deliveries,
task inputs, explicit public close or transport exit are claimed. host_exit is
null. Cleanup reaped Calc 255, Openbox 0 and Xvfb 0. After all were terminal,
independent XLSX read found no nonempty cells; task success is false. The blank
workbook is retained. Dependency/library warnings in original stderr are retained.

Do not treat the contract PASS or portable metadata admission as this live gate
passing. The record remains a failure. A separately frozen construction correction
may use the existing portable read_window_title helper and retain both legacy
and UTF8 title values; it must not rewrite this result or retry its inputs.
Actual model token/billing accounting is not measured in this record.
