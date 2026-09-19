# Repair report: scorer import boundary after #2343

This additive repair branch preserves merged PR #2343 and its failed check.

## H/T/D/C/U

- **H:** The retained scorer tests are valid when the sibling `scorer.py`
  module is importable during package-qualified unittest discovery.
- **T:** Set `PYTHONPATH` to
  `research/integration/live_adapter_effect_scorer_2246_v1` for the existing
  container test-and-score step. No scorer logic or retained evidence is
  changed.
- **D:** On the unmodified main workflow, `python -m unittest discover -s
  research/integration/live_adapter_effect_scorer_2246_v1 -t . -p
  'test_*.py' -v` fails with `ModuleNotFoundError: No module named 'scorer'`.
- **C:** With the path fix, the pinned `python:3.12-slim` container and
  `--network none` run all four scorer tests successfully. The tests cover
  explicit authority, HOLD, fail-closed ambiguity, and missing authority.
- **U/STOP:** The workflow's pinned report URL returns HTTP 404. Therefore no
  retained-evidence score is claimed. This repair establishes neither live
  GUI/model/task utility nor latency or production behavior.

## Reproduction

```text
without PYTHONPATH: ModuleNotFoundError: No module named 'scorer'
with PYTHONPATH: 4 tests, 4 passed
pinned report fetch: HTTP 404
```
