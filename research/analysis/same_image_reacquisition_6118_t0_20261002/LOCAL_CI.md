# Local CI — Issue #6118 T0

Validated on branch `research/6118-same-image-vs-reacquisition-t0-20261002`, based on main `3adec9cdc2cff5ef68f19acd55c5823fcaad26df`. No formal candidate or auditor was rerun for CI.

| Gate | Command / result |
| --- | --- |
| Package construction tests | `python3 -B -m unittest discover -s research/analysis/same_image_reacquisition_6118_t0_20261002 -p 'test_*.py' -v` — 9/9 PASS. |
| Python syntax | `python3 -B -m py_compile research/analysis/same_image_reacquisition_6118_t0_20261002/candidate.py research/analysis/same_image_reacquisition_6118_t0_20261002/audit.py research/analysis/same_image_reacquisition_6118_t0_20261002/test_method.py` — PASS. |
| Analysis Index workflow | `python3 research/analysis/check_index.py` — 340 retained result/failure directories indexed. |
| Analysis workflow companion tests | endogenous-demand T0 8/8; selection-aware shadow-audit T1 12/12 — PASS. |
| Analysis index tests | `python3 -B -m unittest -v research.analysis.test_check_index` — 6/6 PASS. |
| Research Workspace Index workflow | `python3 -B -m unittest discover -s research -p 'test_*workspace*.py' -v` — 21/21 PASS; `python3 research/check_workspace_index.py --git-tree` — 152 namespaces reachable. |
| Public Navigation workflow | `python3 .github/check_public_navigation.py` — 26 documents, 1154 repository-relative links; PASS. |
| #3270 replay Docker workflow | Exact workflow test under local OrbStack Docker with `--network none` and read-only checkout, `python:3.12-slim`; 2/2 PASS. Locally resolved image digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/arm64. This is local Docker evidence, not a GitHub-hosted job result. |
| Diff and package hashes | `git diff --check`; `shasum -a 256 -c SHA256SUMS.txt` — PASS. |

The experimental candidate and independent audit remain exactly one invocation each, as specified in `FREEZE.json`; the test suite uses in-memory synthetic copies and does not read or rewrite the official raw/audit outputs. GitHub Actions status is tracked separately from local CI.
