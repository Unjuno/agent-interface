# Local validation

- Construction checks: `python3.12 -B -m unittest discover -s research/analysis/conditional_parallax_6079_integrity_adjudication_a01_20261003 -p 'test_*.py' -v` — 4/4 passed before freeze; tests use only synthetic mutation examples and never invoke the parent candidate or raw auditor.
- Syntax: `python3.12 -B -m py_compile research/analysis/conditional_parallax_6079_integrity_adjudication_a01_20261003/auditor.py research/analysis/conditional_parallax_6079_integrity_adjudication_a01_20261003/test_adjudication.py` — passed before freeze.
- Frozen raw-only audit: one invocation, exit 0; zero reconstructed data errors; corrected controls 4/4; final disposition `HOLD_PARENT_FORMAL_PROMOTION`; candidate invocations in this allocation 0.
- Repository analysis-index workflow matrix had already passed 105/105 tests under Python 3.12, including the frozen historical workflow-blob check. Adding these four audit-construction tests gives 109/109 across the complete relevant local matrix; no candidate was invoked in this adjudication.
- Parent input/output/source SHA checks, analysis index, this package's manifest, and scoped `git diff --check` are verified after packaging.
