# Local CI — A02 evidence package

Host: macOS 26.6.2 arm64, CPython 3.14.5. The hosted `analysis-index` workflow pins CPython 3.12 on Ubuntu; local results are a pre-merge check, not a substitute for hosted checks.

- `python3 research/analysis/check_index.py --write` updated the generated index to **586** retained result/failure directories; `python3 research/analysis/check_index.py` then passed.
- Reproduced the workflow's frozen-source restoration step from commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd`. The restored workflow matched the required SHA-256 `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2`. The original checkout workflow was restored afterward and its SHA-256 rechecked as `8796902009a9adf830c5a8cf6ae38d2510812ef619e46da255b62003401af80e`.
- Ran all 21 fixed unittest steps from `analysis-index.yml`, plus the new A02 package tests and the index checker: **23/23 local CI steps passed**, **140 unit tests passed**.
- `python3 -m py_compile` for candidate/auditor and `git diff --check` passed.

An initial diagnostic run of the geometry-feasibility tests without the workflow's frozen-source restoration produced 2 expected hash failures against the current workflow file. After executing the workflow's actual pinned-source restoration step, that suite passed 10/10 and the complete matrix passed. The temporary workflow replacement was restored; no unrelated source file was edited.

## Final integration-base recheck

After main advanced to `49cc67de82ed48980245a6e25376bb3ced700a01`, the evidence branch was rebased. The analysis index now covers **590** result/failure directories. The exact pinned workflow restoration and all **23/23 local CI steps / 140 unit tests** passed again on macOS/CPython 3.14.5. The candidate and formal auditor were not rerun; only the tests, generated-index gate and integration diff were rechecked.
