# Local CI record

Validated after incorporating current main `b76078c95543c65940da41b8c967fe1183a2b1df` (T8's scientific freeze remains against main `49144844b482026c33fcfbde7e2fd5f7bdc7762c`). All final commands below exited 0.

- Retained-result index: `python research/analysis/check_index.py` — 454 directories indexed.
- Issue experiment suites: #6469 5/5, #6422 2/2, #6405 7/7, #5702 8/8, #5681 12/12, #6492 T0 4/4, #6492 allocation-02 1/1, #6492 modal baseline 2/2, and this T8 suite 6/6.
- Workspace: `python -B -m unittest discover -s research -p 'test_*workspace*.py' -v` — 21/21; `python research/check_workspace_index.py --git-tree` — 156 top-level directories reachable.
- Public navigation: `python .github/check_public_navigation.py` — 26 documents / 1,380 repository-relative links.
- `git diff --cached --check` — PASS.

The final executed unit-test total is 68. Setup attempts before the final run exposed sparse-checkout/test-discovery conditions, not experiment-source failures: four suites initially collected zero tests before their CI paths were added to sparse checkout; after syncing latest main the #6405 test file was again outside the local sparse view and was materialized before the final rerun; two nested #6492 tests were first invoked from the wrong directory; Public Navigation initially could not see the new untracked evidence path. Sparse paths and invocation working directory were corrected, intended evidence/index files staged, then affected checks rerun. The #6492 allocation-02 command passed when run from its workflow-defined working directory. No unrelated repository file or active container was modified.
