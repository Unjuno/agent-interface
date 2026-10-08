# GPU successor to Issue #3790

Frozen local RTX 3080 experiment comparing rank-2 online, rank-4 online and matched rank-4 batch adaptation across five fresh seeds.

- H/T/D/C/U and frozen gates: parent Issue #3807.
- `runner.py`: exactly one five-seed CUDA invocation; losslessly packed row predictions to stdout.
- `audit.py`: independent offline recomputation.
- `test_construction.py`: construction-only checks; no optimizer updates.
- `FREEZE.json`: exact source hashes/environment/protocol, committed before formal allocation.

No container result, GUI/task effect, model-provider call, or runtime authority claim.