# Full golden route over container-host model IPC: successor #2737

`PASS` — fresh allocation v4, seed `991035`, no retry.

The Docker GUI/runtime completed all six persistent tasks through the
shared-volume container-to-host model IPC boundary. Independent evaluation
reported six records with no duplicates or missing effects. All six submissions
were exact, all releases were verified, and the layout-B invalidation at
task-4 was repaired successfully before tasks 5–6 reused the new target.

The host model remained non-authoritative. The complete raw report is retained
locally at `runtime/results-local/full-golden-ipc-2737-v4/report.json`; only the
compact result and source hashes are committed here. Earlier v1–v3 stops remain
debug evidence: missing IPC environment, then the runner timing-contract
failure (`KeyError('exited_ns')`). They were not selected away from the v4
allocation and are not retries of v4.
