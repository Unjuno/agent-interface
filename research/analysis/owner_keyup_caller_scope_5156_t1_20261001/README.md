# Caller-bracket scope analysis T1

Finite, source-only analysis for Issue #5156. It preserves exact pinned v10/v3 dependencies and distinguishes explicit key-up caller brackets from autonomous owner cleanup.

- `FREEZE.json` pins main, exact Git blob IDs, tool hashes, hypothesis and gates.
- `classify.py` is the one-shot AST classification command.
- `audit.py` independently verifies source identity, callsite classes and scope.
- `results/CLASSIFICATION.json` and `results/AUDIT.json` are the frozen outputs.
- `REPORT.md` records H/T/D/C/U, result and limitations.
- `tests/test_release_bracket.py` contains four host-only construction assertions.

No Docker/X11 allocation was used or consumed. The finding is about control-flow contract scope, not runtime key-up timing or physical/application behavior.
