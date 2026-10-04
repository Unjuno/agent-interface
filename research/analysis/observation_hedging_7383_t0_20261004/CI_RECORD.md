# Local verification record

Environment: macOS 27.0.1 arm64, CPython 3.14.5. OrbStack could not enumerate containers because the Engine returned its known containerd missing-blob error; all listed checks ran on the host. No claim of container isolation.

| Check | Command | Outcome |
|---|---|---|
| Syntax | `python3 -m py_compile candidate.py auditor.py test_package.py` | PASS |
| T0 construction/invariants | `python3 -m unittest research.analysis.observation_hedging_7383_t0_20261004.test_package -v` | PASS, 6/6 |
| Research workspace index unit suite | `python3 -B -m unittest discover -s research -p 'test_*workspace*.py' -v` | PASS, 22/22 |
| Analysis result index | `python3 research/analysis/check_index.py` | exit 0; sparse checkout reported absent sibling directories were not treated as removals. Separately, a Git-tree enumeration matched the generated block against all 649 committed result/failure/STOP directories: complete, sorted and unique. |
| Whitespace | `git diff --check` | PASS |

The complete GitHub Actions analysis-index workflow was not run locally: this is a sparse checkout and OrbStack was unavailable. The focused changed-package tests and the local research-workspace index suite were run. Re-run applicable checks after final commit and verify GitHub PR checks before merge.
