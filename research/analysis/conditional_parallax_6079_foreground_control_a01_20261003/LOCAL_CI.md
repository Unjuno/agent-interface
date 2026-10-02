# Local checks

- Construction: `python3 -B -m unittest discover -s research/analysis/conditional_parallax_6079_foreground_control_a01_20261003 -p 'test_*.py' -v` — 1/1 passed before freeze.
- Syntax: `python3 -B -m py_compile research/analysis/conditional_parallax_6079_foreground_control_a01_20261003/probe.py research/analysis/conditional_parallax_6079_foreground_control_a01_20261003/auditor.py research/analysis/conditional_parallax_6079_foreground_control_a01_20261003/test_control.py` — passed before freeze.
- Full `.github/workflows/analysis-index.yml` Python test matrix rerun locally with its declared Python 3.12: 105 tests passed across the workflow's 17 unittest steps plus this allocation's construction test. The workflow's pinned historical `analysis-index.yml` blob was restored in an isolated temporary directory and matched SHA-256 `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2` before the dependent geometry suite; no checkout workflow file was modified.
- Formal candidate and raw-only auditor: one invocation each, both exit 0; `CONTROL_EXPOSED` independently reconstructed.
- Parent frozen candidate and corpus hashes: verified against the parent manifest/provenance in `FREEZE.json`.
- Repository analysis index passed with 550 indexed result directories; allocation SHA-256 manifest passed; allocation/index `git diff --check` passed.
- GitHub-hosted Actions for the PR head remain queued, so these local results do not claim that the hosted workflow completed.
