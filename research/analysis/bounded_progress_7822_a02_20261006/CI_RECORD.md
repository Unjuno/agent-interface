# Post-run repository checks

- `python3 research/analysis/check_index.py --write`: refreshed the generated index to 757 retained analysis result/failure directories.
- `python3 research/analysis/check_index.py`: PASS, 757/757 directories indexed.
- `python3 research/check_workspace_index.py`: PASS, 160/160 top-level research directories reachable.
- `python3 -B -m unittest discover -s research/analysis -p 'test_check_index.py' -v`: PASS, 17 tests.
- `python3 -B -m unittest discover -s research -p 'test_check_workspace_index.py' -v`: PASS, 1 test.
- `git diff --check`: PASS.

The frozen candidate and auditor were not rerun during these index checks.
