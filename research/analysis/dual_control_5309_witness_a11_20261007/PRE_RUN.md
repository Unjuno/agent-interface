# A11 frozen run protocol

- Allocation: `5309-TOPOLOGY-DEPENDENT-A11-HOST-20261007`.
- Parent research snapshot: A10 head `88aca74fbcda4043c2c96b31007af1473f496c93`; main at intake `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`.
- Runtime: CPython 3.14.5, standard library only.
- Environment choice: host deterministic simulation. Container execution is unavailable in this work session because the previously inspected OrbStack content store rejects an existing blob with `operation not supported`; no container state was pruned or repaired. This experiment uses no GUI, model, network, or OS input.
- Construction tests: `python3 -m unittest -v research/analysis/dual_control_5309_witness_a11_20261007/test_construction.py` (pre-freeze only).
- Input generation: `python3 research/analysis/dual_control_5309_witness_a11_20261007/design.py` (pre-freeze only).
- Formal candidate, once: `python3 research/analysis/dual_control_5309_witness_a11_20261007/candidate.py research/analysis/dual_control_5309_witness_a11_20261007/candidate-input.json research/analysis/dual_control_5309_witness_a11_20261007/candidate-choices.json`.
- Formal environment, once: `python3 research/analysis/dual_control_5309_witness_a11_20261007/environment.py research/analysis/dual_control_5309_witness_a11_20261007/candidate-input.json research/analysis/dual_control_5309_witness_a11_20261007/candidate-choices.json research/analysis/dual_control_5309_witness_a11_20261007/oracle.json research/analysis/dual_control_5309_witness_a11_20261007/candidate-raw.json`.
- Formal auditor, once: `python3 research/analysis/dual_control_5309_witness_a11_20261007/auditor.py research/analysis/dual_control_5309_witness_a11_20261007/candidate-input.json research/analysis/dual_control_5309_witness_a11_20261007/candidate-choices.json research/analysis/dual_control_5309_witness_a11_20261007/candidate-raw.json research/analysis/dual_control_5309_witness_a11_20261007/oracle.json research/analysis/dual_control_5309_witness_a11_20261007/audit.json`.

The source, generated input/oracle, and construction test are frozen by `FREEZE.md` before any formal command. Candidate and environment receive only their declared file paths, but because all files share the host filesystem this is process/protocol separation, not a security boundary. No formal reruns are permitted; any defect is preserved as the allocation's result and may motivate a separately frozen successor.
