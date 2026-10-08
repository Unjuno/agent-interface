# #2254 allocation02 retention-envelope supplement

Allocation `live-scheduler-2254-r1-20260922-02` continues the exact scientific question and frozen thresholds from allocation01 after its `STOP_OUTER_EXECUTION_TIMEOUT`. It is not a new Issue and does not reinterpret allocation01.

Scientific source, schedules, policies, service time and decision gates are unchanged. Engineering-only delta:
- one fresh live case per external `case_runner.py` invocation;
- each completed case is written immediately to its own immutable JSON file;
- `assemble.py` requires the exact 18 identities (6 families x 3 reps) before creating the audit input;
- missing/failed case stops later dispatch; no retry/replacement/pooling.

Excluded wrapper construction executed each of the six case families once with rep0. Each completed in 3.00–3.43s; every watcher, three actors and Xvfb exited 0. No formal02 case has run at this freeze.

The frozen science gates remain: service 8ms/item; critical deadline 100ms; fairness burst 3; selected B noncritical bound 50ms; CRITICAL_HEAD_FIRST starvation floor 70ms. Parent #2254 still requires a later actual model/task/effect allocation even if this component allocation passes.
