# Issue #57 ProspectiveRun synthetic successful task/effect join — R05

## Conditions
Windows CPython 3.13.14; Pillow 12.2.0. One frozen `plain/task-1` synthetic assignment and fresh local registered durable custodian. A fixed fake model result supplies one complete usage row. The compiled executor is patched to return a retained successful execution receipt; the independent fixture scorer reports exact saved effect and release. No provider, GUI, native input, Docker, WSL, or live dispatch.

PASS only if the v3 caller returns `TASK_SUCCEEDED`, execution and effect receipts persist, custody audit validates every usage/receipt join, the task adapter emits a valid `projected` frozen-v1 row, and run finalization stays HOLD with the other 17 assignments missing. Run the whole focused module normally and under `-O`.

## Result
The module passes 5/5 normally and 5/5 under `-O`. The synthetic success row projects successfully; both durable execution and effect receipts pass custody audit. Finalization correctly remains HOLD for the 17 unassigned tasks, and the manifest still has `dispatch_enabled: false`.

## Scope limits
The successful model output, executor receipt and scorer are all synthetic callbacks. This proves a local success-shaped composition and projection path only. It does not prove real provider usage, a real saved effect, live GUI/input/release, a complete 18-task three-arm comparison, or efficiency. Keep #57 open.
