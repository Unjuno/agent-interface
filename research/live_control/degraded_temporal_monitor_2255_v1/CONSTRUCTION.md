# Excluded construction record

Formal allocation `degraded-temporal-monitor-2255-20260922-01` has executed **0/16** cases at this freeze.

Construction/debugging is excluded from the formal denominator:

1. Initial unit invocation from outside the study directory failed to import local `policy.py` (`ModuleNotFoundError`). Source unchanged; rerunning the test from the declared study cwd passed 7/7.
2. `construction/ab`: observer launched with `python -S`, so installed Python-Xlib was unavailable. STOP before a usable live event row.
3. `construction2/ab`: observer subscribed to Tk's inner `winfo_id()` while `WM_NAME` lived on the top-level wrapper; event wait timed out. No formal case.
4. `construction3/ab_within`: wrapper targeting succeeded, but Python-Xlib returned `WM_NAME` as `str` and the observer attempted `bytes(value)` without an encoding. STOP before a complete case.
5. `construction4`: all eight frozen scientific schedules completed once with zero app/observer/Xvfb exits. Observed policy/oracle pattern matched the preregistered table, including declared-gap UNKNOWN and undeclared-gap false SATISFIED. These rows remain construction only and are not pooled into formal evidence.

All engineering corrections above precede this source freeze. No formal source, threshold, schedule, or result has been consumed.
