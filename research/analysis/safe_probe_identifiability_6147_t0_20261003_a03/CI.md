# Local CI record

Repository checks on the additive evidence package and its navigation:

- `python3 -I research/analysis/check_index.py` — PASS, 538 retained result/failure directories indexed.
- `python3 -I research/check_workspace_index.py` — PASS, 156 top-level research directories reachable.
- `python3 -I -m unittest discover -s research/analysis -p 'test_check_index.py' -v` — PASS, 6 tests.
- `python3 -I -m unittest discover -s research -p 'test_check_workspace_index.py' -v` — PASS, 1 test.
- `python3 -I -m py_compile .../candidate.py .../auditor.py` — PASS (syntax/bytecode compilation only; not a formal rerun).
- `git diff --check` — PASS.
- `python3 -I .github/check_public_navigation.py` — PASS, 26 documents and 1,536 repository-relative links, after staging so the tracked-link gate could resolve the new report path.

No GitHub Actions workflow was run locally or modified. Repository runtime,
container, model, GUI, and product integration suites are outside this synthetic
analytical allocation's claim and were not represented as passing.
