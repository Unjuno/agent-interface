# Issue #5044 — queue-cost import-boundary successor

This additive allocation follows #5021 after its retained report disclosed that
`heapq` was first imported after the process-CPU timer began. It does not edit,
replace, or pool #5021 or #5025 evidence. The #5025 x86_64 worker already imports
`heapq` at module load; this allocation isolates the ARM64 #5021 measurement
boundary using the exact same immutable candidate schedule.

The hypothesis, thresholds, controls, container identity, and limits are frozen
in the GitHub Issue and `src/FREEZE.json` before either formal container runs.
The primary metric is paired process CPU for queue construction plus complete
drain; process startup, module import, input parsing, and serialization are
recorded or excluded. `heapq` must be present in `sys.modules` before each
worker timer begins. There is no warm-up call.

Expected runner command inside the pinned local OrbStack image:

```text
python -B /src/runner.py --input /input/scenarios.json --formal /out
```

The independent raw-only auditor runs once in a separate network-disabled
container after the runner exits. See `results/formal01/REPORT.md` and the
adjacent raw/audit receipts for the actual disposition. The result is bounded to
this synthetic queue schedule and one Python/Linux/arm64 environment; it is not
a production scheduler recommendation.
