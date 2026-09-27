# Issue #5021 — candidate-queue cost crossover

This is a separate measured-cost successor to the semantics-only scheduler
result retained for #2868/#4978. It does not alter the prior allocations.

Before execution, `FREEZE.json` binds the deterministic schedule, source hashes,
exact OrbStack image, one-shot runner/auditor commands, CPU/memory limits, and
the decision threshold. The only timed work is queue construction and a full
drain of all-ready candidates under one fixed stable key. The three policies
must produce the exact same order. All process stdout/stderr and full traces
are retained in the raw result.

The experiment is not yet run. A previous PASS/FAIL remembered from another
allocation is not a result for this allocation. `results/formal01/runner/` and
`results/formal01/audit/` must be empty before the sole runner invocation.
Any STOP or negative threshold result is preserved as observed.

Run the preformal construction checks with:

```sh
python3 -m py_compile research/coordination/scheduler_cost_scaling_2868_v1/*.py
python3 research/coordination/scheduler_cost_scaling_2868_v1/test_protocol.py -v
python3 research/check_workspace_index.py
git diff --check
```

The formal command and separate raw-only audit command are recorded verbatim
in `FREEZE.json`; do not rerun either after the one-shot invocation.
