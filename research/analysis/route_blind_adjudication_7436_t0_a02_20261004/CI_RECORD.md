# Local checks — A02

- Construction: `python3 -I -B -m unittest discover -s research/analysis/route_blind_adjudication_7436_t0_a02_20261004 -p 'test_package.py' -v` — 6/6 PASS before formal candidate.
- Python byte-compilation of presenter/candidate/auditor/tests — PASS.
- `git -c core.whitespace=cr-at-eol diff --check` — PASS.
- Candidate formal invocation: once, exit 0.
- Independent auditor formal invocation: once after candidate exit 0, exit 0, 8/8 effective mutations rejected.
- Analysis-index tests: 17/17 PASS. Sparse-aware `python3 research/analysis/check_index.py` exited 0 and explicitly reported that absent sibling paths were not treated as removals; this sparse checkout does not prove full-index currentness.
- Workspace-index tests: 1/1 PASS. `python3 research/check_workspace_index.py --git-tree`: PASS, 159 top-level directories reachable.
- Full repository CI and GitHub Actions were not run locally; no workflow was changed.

The first sparse-checkout analysis-index check correctly failed because the manually added A01 index path included a nonexistent `_20261004` suffix. The tracked A01 package directory is `route_blind_adjudication_7436_t0_a01` (without the date), while A02 includes its date. The index link was corrected; no result/source data changed.

The first committed-tree workspace-index invocation exited 2 with `GIT_COMMAND_FAILED` because this partial clone had not materialized the `research/` tree and index blob objects required by the script's no-lazy-fetch check. Reading the exact committed tree entry and two index blobs through Git then made the unchanged check pass; no source checkout files were altered by that object fetch.
