# Local checks

- Construction: `python3 -B -m unittest discover -s research/analysis/conditional_parallax_6079_foreground_control_a01_20261003 -p 'test_*.py' -v` — 1/1 passed before freeze.
- Syntax: `python3 -B -m py_compile research/analysis/conditional_parallax_6079_foreground_control_a01_20261003/probe.py research/analysis/conditional_parallax_6079_foreground_control_a01_20261003/auditor.py research/analysis/conditional_parallax_6079_foreground_control_a01_20261003/test_control.py` — passed before freeze.
- Formal candidate and raw-only auditor: one invocation each, both exit 0; `CONTROL_EXPOSED` independently reconstructed.
- Parent frozen candidate and corpus hashes: verified against the parent manifest/provenance in `FREEZE.json`.
- Repository analysis index, manifest hashes and whitespace checks: run after adding the report and index entry.
