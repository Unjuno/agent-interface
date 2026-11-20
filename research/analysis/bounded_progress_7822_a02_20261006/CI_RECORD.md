# Post-run repository checks

- `python3 research/analysis/check_index.py --write`: refreshed the generated index to 757 retained analysis result/failure directories.
- `python3 research/analysis/check_index.py`: PASS, 757/757 directories indexed.
- `python3 research/check_workspace_index.py`: PASS, 160/160 top-level research directories reachable.
- `python3 -B -m unittest discover -s research/analysis -p 'test_check_index.py' -v`: PASS, 17 tests.
- `python3 -B -m unittest discover -s research -p 'test_check_workspace_index.py' -v`: PASS, 1 test.
- `git diff --check`: PASS.

After rebasing the evidence branch onto current main `a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028` (which added the integrated #7799 result), the analysis index passed at 758/758 directories; the same 17 analysis-index tests and 1 workspace-index test passed again. Workspace reachability remained 160/160. The formal roles were not rerun.

The frozen candidate and auditor were not rerun during these index checks.
