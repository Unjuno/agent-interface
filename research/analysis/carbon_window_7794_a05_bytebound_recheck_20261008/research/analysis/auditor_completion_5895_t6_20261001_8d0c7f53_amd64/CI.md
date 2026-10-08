# Local CI and verification

All checks were run locally after the formal candidate and independent auditor completed; no GitHub Actions run is claimed.

## Package and frozen-target tests

- `cd source && python3.12 -B -m unittest discover -s tests -v`: **10/10 PASS**.
- `cd source/target && python3.12 -B -m unittest discover -s . -p 'test_*.py' -v`: **11/11 PASS**.
- `python3.12 -m py_compile source/*.py source/target/*.py`: **PASS**.
- `sh -n host_tools/*.sh`: **PASS**.
- `python3.12 -B -m unittest discover -s . -p 'test_*.py' -v` from `source/target`: **11/11 PASS**. An initial invocation from `source/` exposed that the frozen upstream test reads `EXPECTED.json` relative to cwd; running at its intended target directory passed without modifying frozen source.
- The first package test invocation from repository root failed to import package-local modules; corrected invocation from `source/` passed 10/10. This was test-discovery context only, not a test failure.

## Repository CI targets

- Analysis-index workflow suites: **8/8** and **12/12 PASS**.
- `python3.12 research/analysis/check_index.py --write`, then read-only check against integrated current main: **329 retained result/failure directories indexed, PASS**.
- Analysis-index checker tests: **6/6 PASS**.
- `python3.12 -B -m unittest discover -s research -p 'test_*workspace*.py' -v`: **21/21 PASS**; `python3.12 research/check_workspace_index.py --git-tree`: **152 top-level directories reachable, PASS**.
- Public navigation: **26 documents, 1138 repository-relative links, PASS** against integrated current main after staging the additive package so the checker could resolve its generated index link.
- `git diff --cached --check`: **PASS** after removing incidental trailing spaces from the new preregistration copy and copied STOP transcription; original GitHub STOP comment is linked above and unmodified.
- Package `SHA256SUMS`: **76 files verified**. No hosted CI is claimed; required GitHub checks will be read after PR creation.
