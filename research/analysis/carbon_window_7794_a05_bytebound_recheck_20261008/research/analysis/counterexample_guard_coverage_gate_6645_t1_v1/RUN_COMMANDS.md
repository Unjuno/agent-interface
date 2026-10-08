# Exact execution commands

Construction before freeze:

```sh
python -B -m unittest discover -s research/analysis/counterexample_guard_coverage_gate_6645_t1_v1 -p 'test_*.py' -v
python -m py_compile research/analysis/counterexample_guard_coverage_gate_6645_t1_v1/candidate.py research/analysis/counterexample_guard_coverage_gate_6645_t1_v1/auditor.py
```

Formal allocation (exactly once; run only after freeze verification):

```sh
bash research/analysis/counterexample_guard_coverage_gate_6645_t1_v1/run_formal.sh
```

The runner starts one candidate and one auditor container, separately, with
network disabled and the pinned cached image. It stores pre/post Docker inspect
data, IDs, raw candidate output, auditor output, stderr and exit codes. A failed
formal command is terminal for this allocation; do not rerun it.
