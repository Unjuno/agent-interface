# V39 cleanup race A01: down-return lineage registration

## H / T / D / C / U

- **H:** If cancellation cleanup is published during the return window of the owner `down` call, the A02 bridge drains it before registering the admission lineage. The cleanup is then unscoped and a later `NOOP_ALREADY_UP` can be emitted as a second receipt.
- **T:** Run a deterministic owner stub whose `call("down")` returns the admission and publishes a matching confirmed-up cleanup record before control returns to the bridge. Then call `raw("F8", False)` to exercise the late no-op.
- **D:** PASS only when the admission is emitted first, followed by exactly one cleanup release carrying the same actuation, run/step and token; no unscoped or duplicate no-op row is allowed.
- **C:** One deterministic owner/bridge boundary interleaving. The test isolates event ordering and lineage registration; it is not an execution-frequency estimate.
- **U:** Synthetic owner stub and fake display harness only. No live X11, OS input, GUI/game, model, application effect, useful feedback, recovery benefit, or MAP01 progress.

## Result

The previously published A02 source remains byte-for-byte preserved at its original path. The additive successor moves cleanup draining after down-admission context registration and emission. The deterministic regression now produces `input_admission` then one contextual `CONFIRMED_PHYSICAL_UP`; the subsequent no-op is suppressed. The prior implementation's three-row outcome (unscoped cleanup, admission, duplicate no-op) is preserved in PR discussion #5984715563.

Five tests (the three bridge tests, shutdown cleanup, and execute-context cleanup) passed under normal Python and optimized Python 3.12.11. The initial packaging attempt that omitted the frozen executor dependency is retained as `ATTEMPTS.json`; it failed during import before any test ran. No one-shot A01/A03 candidate was rerun.

## Reproduction

From the repository root, use the pinned `python:3.12.11-slim` image (digest in `FREEZE.json`) with network disabled, read-only root, and a temporary writable `/tmp`:

```sh
python -B -m unittest -v research.doom.map01_v39_down_return_cleanup_race_a01_20261005.test_bridge research.doom.map01_v39_down_return_cleanup_race_a01_20261005.test_teardown research.doom.map01_v39_down_return_cleanup_race_a01_20261005.test_execute_context
python -O -B -m unittest -v research.doom.map01_v39_down_return_cleanup_race_a01_20261005.test_bridge research.doom.map01_v39_down_return_cleanup_race_a01_20261005.test_teardown research.doom.map01_v39_down_return_cleanup_race_a01_20261005.test_execute_context
python research/doom/map01_v39_down_return_cleanup_race_a01_20261005/audit.py
```

All frozen fixtures and imports needed by the focused tests are included under `SOURCE/`. The result supports only the deterministic construction gate; the live #59 measurement and bounded-recovery objectives remain open.
