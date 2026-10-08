# Current-main V39/V15 regression follow-up A02

## H/T/D/C/U

**H.** The exact current-main production source for V39 cover monitoring, cancellation/release handling, V15 session flow, Executor V13, and explicit-UP cancellation remains regression-clean under the focused source/fake-X suite.

**T.** Freeze: current `main` commit `b4046798ed8902745a36e8fda091204233bb06d3`. Run the seven focused test modules listed in `FREEZE.json` under the bundled CPython 3.12.14 runtime, normally and with `-O`. The saved stdout/stderr logs are `normal.log` and `optimized.log`. `SOURCE_CLOSURE.json` records 73 statically discovered repository files imported from those test roots, with Git blob IDs at the tested commit and comparison to the earlier regression baseline `74fc81e0a447ad05e4a2220b16d7949979635fb9`.

**D.** PASS only if both commands finish with 107 tests run and `OK`, and every recorded source-closure blob resolves at the frozen commit.

**C.** This is model-free source and fake-X regression evidence. It checks existing controller and input-owner contracts; it does not run a real X server or modify production code. Static AST import traversal does not identify dynamic imports or runtime-loaded resources.

**U.** It does not establish physical key state, game consumption, live threat response, useful task effect, recovery efficacy, latency under a model, or MAP01 completion. The separate live threat gate remains HOLD and unassigned.

## Result

The seven modules pass **107/107 normally and 107/107 under optimized Python** on the frozen current-main source snapshot. Static closure comparison found 73 files; the only blob change since the earlier regression baseline is the additional explicit-UP cancellation test module. All production source blobs in the closure are unchanged. `audit.py` independently verifies the saved run summaries and exact Git blob identities.

No game, GUI, model, OS input, X server, or live allocation was started. See `FREEZE.json`, `RESULT.json`, `SOURCE_CLOSURE.json`, `COMMANDS.txt`, the two logs, and `AUDIT_V2.json` for retained details.
