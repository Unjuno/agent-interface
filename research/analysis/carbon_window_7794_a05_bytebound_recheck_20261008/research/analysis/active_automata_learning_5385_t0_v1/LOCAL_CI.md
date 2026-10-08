# Local CI — Issue #5385 T0

Run after the formal raw and audit were immutable and the evidence package was staged.

- `python research/analysis/check_index.py --write`: PASS; after rebasing onto newer main, refreshed to 204 retained analysis result/failure directories (201 at the initial base, plus three mainline additions).
- `python research/analysis/check_index.py`: PASS; 204 indexed.
- `python .github/check_public_navigation.py`: PASS; 26 documents, 897 repository-relative links after rebasing onto newer main. The first attempt before staging correctly reported the three new tracked targets as missing; after staging it passed.
- `python -m py_compile research/analysis/active_automata_learning_5385_t0_v1/experiment.py research/analysis/active_automata_learning_5385_t0_v1/audit.py`: PASS.
- `python research/check_workspace_index.py`: cannot pass in this sparse checkout because most pre-existing top-level research directories are intentionally not hydrated. The full-checkout GitHub workflow is required; sparse-checkout omissions are not represented as a repository defect or a pass.
- `git diff --check`: PASS (to be rerun after final staging).

No formal simulator or auditor rerun was performed for these documentation/index checks.
