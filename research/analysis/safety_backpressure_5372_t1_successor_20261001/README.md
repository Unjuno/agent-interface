# Issue #5372 T1 successor (allocation 02)

This folder contains only the new allocation identity envelope and its tests. The deterministic simulator and independent event auditor remain frozen in `../safety_backpressure_5372_t1_v1/`; allocation 01's runner STOP is retained at that predecessor path. `candidate.py` loads that exact simulator, changes the emitted allocation ID to 02, and runs the same 16 cells. `audit_successor.py` checks the new identity and then delegates to the exact frozen raw auditor.

The T1 question is whether fast local action can create endogenous verifier overload, stale evidence and retries, and whether pressure admission mitigates the specific measured inversion without violating mandatory safety service. This is not a production workload benchmark and does not test all policy variants in Issue #5372, including its route-set expansion contrast. The separately merged #5702 task-choice rebound experiment is context only; its events, measures, and conclusions are not pooled here.

Local construction CI:

```sh
python3 -m py_compile research/analysis/safety_backpressure_5372_t1_successor_20261001/*.py
python3 -m unittest discover -s research/analysis/safety_backpressure_5372_t1_successor_20261001 -p 'test*.py' -v
python3 research/analysis/safety_backpressure_5372_t1_successor_20261001/candidate.py research/analysis/safety_backpressure_5372_t1_v1/simulate.py | python3 research/analysis/safety_backpressure_5372_t1_successor_20261001/audit_successor.py /dev/stdin research/analysis/safety_backpressure_5372_t1_v1/audit.py
```

Host test output is construction evidence only. Formal candidate and independent audit are each run once in separate isolated containers; no retry.
