# Issue #7436 T0 successor A02

A01 is preserved unchanged as `FAIL_SETUP_ENTRYPOINT`: Python isolated mode did not import the same-directory module and candidate logic never ran. A02 uses a separate path and seed and explicitly adds the package directory to `sys.path` before the candidate import. It is a new allocation; it does not retry or regrade A01.

This T0 tests only synthetic route-canary masking, score-commit custody, deterministic ordering, and mutation sensitivity. No human, model, GUI, provider, or live route is involved. A method-scoped PASS does not test whether human route-revealed scoring is biased.

See `PREREGISTRATION.md`, `PRELAUNCH_FREEZE.json`, `CONSTRUCTION_RECORD.md`, and (after the one-shot run) `REPORT.md` and raw `results/`.
