# Local validation record for batch branch

Validation was run against the staged publication set in the sparse local
checkout. The first checks and their outcomes are retained below.

| Check | Result | Notes |
|---|---|---|
| `python .github/check_public_navigation.py` (first attempt) | FAIL | New report links pointed to files that were not yet tracked; no link-target typo was reported. |
| `python .github/check_public_navigation.py` (after staging) | PASS | 26 documents, 877 repository-relative links. |
| `python research/check_workspace_index.py` | LOCAL HOLD | The checkout sparsity omitted most existing top-level `research/` directories, so the checker correctly listed them as missing from this filesystem. The repository tree itself was not changed to fake these directories, and the broad multi-gigabyte research tree was not hydrated just for this check. Hosted full-checkout workflow remains required. |
| `python research/analysis/check_index.py` | PASS | 197 retained result/failure directories indexed; this PR adds nothing under `research/analysis/`. |
| `git diff --cached --check` | PASS after correction | Initially identified three extra blank lines at EOF in reports; removed, then rerun against the staged patch. |
| T2 construction smoke | PASS | Exact output and pinned-container context in [`EXECUTION.md`](EXECUTION.md); separate from the one-shot formal allocation. |

No runtime implementation, dependency, or test file outside this research
bundle was modified. Hosted CI should decide the full-checkout workspace-index
gate; a local sparse-checkout HOLD is not relabeled as a repository failure.
