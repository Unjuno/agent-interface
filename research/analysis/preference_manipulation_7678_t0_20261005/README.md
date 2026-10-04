# Preference-certificate manipulation sensitivity — T0

This package tests Issue #7678's finite, non-authoritative hypothesis against the exact frozen `evaluate()` function from the #6274 candidate. It does not rerun the #6274 study, reuse its result allocation, or alter its retained HOLD/PASS record.

## Result

See [`results/formal-01/REPORT.md`](results/formal-01/REPORT.md) for the candidate outcome, independent rank-vector audit, raw JSON, run record, and hashes. The unit of inference is the frozen synthetic fixture and the explicitly declared `possible_frontier` opportunity-set utility. It says nothing about actual human behavior or whether information should be withheld.

## Reproduce

Run `python -B -m unittest discover -s . -p test_construction.py -v` for construction checks. The formal candidate and auditor were each run exactly once in sequence by `run_formal.ps1`; the exact source revision and procedure are in `FREEZE.json`, `COMMANDS.txt`, and `results/formal-01/RUN.json`. Do not rerun allocation `PREFERENCE-MANIPULATION-7678-T0-20261005-01`; preserve its raw outputs.

The candidate loads the frozen #6274 source blob from Git and calls only its pure `evaluate()` function. It writes exclusively beneath this package's `results/formal-01/`. The auditor independently enumerates weak orders by rank vectors and reconstructs completions, frontiers, controls, and manipulation classifications without importing `candidate.py` or the frozen implementation.
