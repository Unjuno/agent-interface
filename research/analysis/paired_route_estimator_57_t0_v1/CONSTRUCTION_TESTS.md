# Construction checks — Issue #57 paired ledger T0

```powershell
python -B -m unittest research.analysis.paired_route_estimator_57_t0_v1.test_t0 -v
```

Local Python 3.12: 15/15 checks pass. The tests cover exact null/planted values,
all-attempt denominators, paired/unpaired summaries, hard safety gating and
seven mutation controls. These are construction checks, not the formal Docker
result and not live #57 performance evidence.

Docker Desktop is running on the local Windows host, but its selected
`desktop-linux` endpoint and `docker desktop status` CLI calls did not return
within the 30-second command window. No daemon restart or context switch was
attempted. The frozen formal allocation therefore uses pinned, isolated Docker
containers on a GitHub-hosted runner and retains the engine and container
inspection records, including STOP outcomes.
