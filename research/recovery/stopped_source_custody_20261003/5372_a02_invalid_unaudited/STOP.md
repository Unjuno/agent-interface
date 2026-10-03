# A02 formal run STOP (not a PASS)

This allocation was started in error while the user's explicit selection was #6749. Do not treat this result as an authorized continuation, a validated #5372 outcome, or a completed experiment. No PR was opened and no main branch changes were made.

The one WSLc candidate invocation exited 0 and its raw output is retained in `formal_01_20261003/candidate/raw.json` (SHA-256 `15f00404f9b12ea87726dde5f927a2e068b1325284d519ac1814cb7034ec222f`). The independent auditor was launched once but exited 2 before Python ran: its command used `/src/backpressure_priority_fairness_5372_a02_20261003/audit.py` although the read-only bind mount exposed the experiment directory itself at `/src`, so the correct path would have been `/src/audit.py`. The recorded stderr is retained in `formal_01_20261003/auditor-attempt.stderr.txt`. Per the preregistered one-shot/no-retry rule, no auditor retry or candidate rerun is permitted for this allocation. Disposition: `STOP_AUDITOR_LAUNCH_PATH_ERROR`; audit outcome unavailable; no PASS/FAIL method claim.

WSLc emitted its warning that swap-limit capabilities/cgroup are unavailable; although 256 MiB was requested, effective memory enforcement is not claimed. The container was requested with CPU=1, network=none, pull=never and was removed on exit. No runtime/product/authority inference is supported.

The host construction suite passed 4/4 before freeze; those checks do not replace the failed formal independent audit. Candidate numbers in the raw file are unadjudicated exploratory output only.

