# Local CI record

Local checks for this evidence-only addition:

- `python3 -m unittest discover -s research/analysis/conditional_parallax_6079_t0_v1_20261003 -p 'test_*.py' -v` — 6 tests passed before freeze; rerun after current-main fast-forward.
- `python3 -m py_compile research/analysis/conditional_parallax_6079_t0_v1_20261003/fixture.py research/analysis/conditional_parallax_6079_t0_v1_20261003/candidate.py research/analysis/conditional_parallax_6079_t0_v1_20261003/auditor.py research/analysis/conditional_parallax_6079_t0_v1_20261003/test_method.py` — passed before freeze; rerun after current-main fast-forward.
- `python research/analysis/check_index.py --write` followed by `python research/analysis/check_index.py` — update/check the generated result-directory index.
- `cd research/analysis/conditional_parallax_6079_t0_v1_20261003 && shasum -a 256 -c SHA256SUMS.txt` — verify frozen sources, inputs, formal outputs, and logs.
- Separately verify the final report/index and whole-tree whitespace/integrity checks after authoring.
- `git diff --check` and repository-specific workflow checks — run after index refresh and current-main fast-forward.

The repository's `.github/workflows/analysis-index.yml` runs the analysis index checker and a fixed suite of unrelated retained-result construction tests on Ubuntu/Python 3.12. It restores a historical workflow blob and verifies its digest, which cannot be faithfully reproduced by the host-only local gate without performing that network fetch. This change does not edit workflow definitions. The issue-specific tests, syntax, index, hashes, and whitespace checks are run locally; the remote workflow remains an additional PR check, not a substitute for the local gate. Final current-main validation: all 6 issue-specific tests passed; `py_compile` passed; analysis index passed at 549 retained result directories; all 14 frozen source/input/output/log SHA-256 entries verified; `git diff --check` passed. The earlier pre-merge SHA command with an empty process-substitution input returned an expected format error and verified no files; the correct manifest-based verification above passed.
