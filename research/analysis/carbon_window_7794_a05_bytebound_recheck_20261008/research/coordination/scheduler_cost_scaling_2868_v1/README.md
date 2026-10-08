# Issue #5021 — candidate-queue cost crossover

This is a separate measured-cost successor to the semantics-only scheduler
result retained for #2868/#4978. It does not alter the prior allocations.

Before execution, `FREEZE.json` binds the deterministic schedule, source hashes,
exact OrbStack image, one-shot runner/auditor commands, CPU/memory limits, and
the decision threshold. The only timed work is queue construction and a full
drain of all-ready candidates under one fixed stable key. The three policies
must produce the exact same order. All process stdout/stderr and full traces
are retained in the raw result.

Allocation 01 has run once. Its independent audit decision is
`FAIL_HEAP_COST_THRESHOLD_NOT_MET`; the complete raw rows, separate-container
audit, exact invocation receipts, scope caveat, and hashes are retained in
`results/formal01/`. No retry was made. The outcome is specific to this frozen
Python implementation; the report identifies a timed `heapq` import that is a
confounder for interpreting representation cost.

Run the preformal construction checks with:

```sh
python3 -m py_compile research/coordination/scheduler_cost_scaling_2868_v1/*.py
python3 research/coordination/scheduler_cost_scaling_2868_v1/test_protocol.py -v
python3 research/check_workspace_index.py
git diff --check
```

The formal command and separate raw-only audit command are recorded verbatim
in `FREEZE.json`; do not rerun either after the one-shot invocation.
