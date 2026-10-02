# Local CI record

Date: 2026-10-03 (JST). Source HEAD used by A03 formal run and this CI: `37b973cd28e20b52950f6e5b75668b76f5d4bd65`.

The first local analysis-workflow test pass was run against the current-main `.github/workflows/analysis-index.yml` without replaying the workflow's historical-source restore step. Two unrelated Issue #6590 provenance tests therefore failed on the expected old workflow hash. Following the workflow itself, the exact frozen workflow at commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd` was temporarily restored for local validation; SHA-256 `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2`. The two affected test groups then passed. The current-main workflow was restored byte-for-byte afterward (SHA-256 `8796902009a9adf830c5a8cf6ae38d2510812ef619e46da255b62003401af80e`); no workflow change is part of this research patch.

On the latest local main (`aeae0edea4e3aba67329e524abd5901b3602dd02`), with the historical test prerequisite reproduced, all commands from the current analysis-index job passed: retained-result index (582 directories), every listed unittest group including A03's 5/5 construction tests, and the current workspace-index job's 21/21 unittests plus namespace check (156 directories). `git diff --check` passed. The final explicit workspace checks also passed after restoring the current workflow file.

This records local CI only. GitHub-hosted checks have not been run or inferred from it.
