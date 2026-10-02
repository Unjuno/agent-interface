# Exact commands

Construction before freeze:

```sh
python -B -m unittest discover -s research/analysis/counterexample_guard_coverage_gate_6645_t1b_v1 -p 'test_*.py' -v
python -m py_compile research/analysis/counterexample_guard_coverage_gate_6645_t1b_v1/candidate_input/candidate.py research/analysis/counterexample_guard_coverage_gate_6645_t1b_v1/auditor.py
bash -n research/analysis/counterexample_guard_coverage_gate_6645_t1b_v1/run_formal.sh
```

Formal allocation, after verifying `FREEZE.sha256`, exactly once:

```sh
bash research/analysis/counterexample_guard_coverage_gate_6645_t1b_v1/run_formal.sh
```

The runner creates one candidate and one independent auditor container. Any
nonzero formal result is terminal; do not rerun.
