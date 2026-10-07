# Local CI and delivery checks

Run on the detached worktree after the T0 outputs were retained and after fast-forwarding the packaging worktree to main `f1747cac5101087ab8c7bc3a226dfdaccf5b6c9e`.

| Check | Runtime | Result |
|---|---|---|
| `python3.12 research/analysis/check_index.py` | CPython 3.12 | PASS — 671 retained result/failure directories |
| `python3.12 -B -m unittest discover -s research/analysis -p test_analysis_checkout.py -v` | CPython 3.12 | PASS — 3/3 |
| `python3.12 -B -m unittest discover -s research -p 'test_*workspace*.py' -v` | CPython 3.12 | PASS — 22/22 |
| `python3.12 research/check_workspace_index.py --git-tree` | CPython 3.12 | PASS — 159 top-level research directories |
| `node --check candidate.mjs`, `node --check audit.mjs`; parse fixtures and retained JSON outputs | Node host | PASS |
| `git diff --check` | Git | PASS for tracked changes (generated analysis index only) |

The frozen candidate and auditor themselves also each passed once in the pinned OrbStack container; see `RUN.json` and `formal_01/`. The entire hosted `Analysis Index` workflow was not replayed locally: it includes unrelated retained-study simulation/replay commands and a historical workflow-blob restore. Those broader workflow checks remain for hosted CI on the reviewable delivery. No historical result directory was replayed or overwritten here.
