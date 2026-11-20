# Construction attempt ledger

- Attempt 1 command: `python -B -m unittest discover -s research/doom/owner_measurement_59_intent_token_successor_I80 -v`. Result: 14 tests, one failure in inherited `test_composed_controller_selects_only_the_measured_session`; candidate helper regression and other builder cases passed. Failure was a POSIX expected-path literal versus Windows host path representation.
- Attempt 2 used the same command after adding the original import-probe test module. Result: 16 tests, three failures: the path expectation and two import-probe cases because their companion `probe_imports.py` was absent from the additive package. This was an incomplete test fixture package.
- Attempt 3 used the same command after normalizing the two fixture expectations with `Path.resolve()` and copying exact `probe_imports.py` source from current main. Result: 16 tests passed. Complete stdout/stderr is retained in `CONSTRUCTION_CI.txt`.

No earlier native/X11 allocation was replayed. These host test iterations only repaired the test package and its platform-specific expected paths.
