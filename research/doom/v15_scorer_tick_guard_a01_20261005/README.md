# V15 scorer input-integrity guard A01

This follow-up repairs a source-contract gap in the opt-in V39 measurement
session from PR #7843. That session selects `session_map01_v15.py`; its scorer
used `int(...)` for episode tics, progress counters, and tic rate. Boolean or
fractional values could therefore be silently converted into plausible score
inputs, and invalid rates could contaminate timeout fallback calculations.

## H / T / D / C / U

- **H:** Exact selected V15 scorer code accepts Boolean/fractional/negative
  counters and tic rates by coercing them with `int(...)`.
- **T:** AST-isolated regression against the exact selected V15 source. Reject
  malformed tic, kill/death, and terminal-flag values; preserve exact controls.
  No game, model, GUI, display, or OS input is initialized.
- **D:** The baseline fails all malformed-input checks. The candidate passes
  focused tests in normal and optimized Python.
- **C:** This is deterministic scorer-contract evidence. It does not establish
  ViZDoom's actual return types or the end-to-end V39/V15 process composition.
- **U:** No useful-feedback attribution, threat response, recovery, live
  allocation, or MAP01 outcome is measured. The existing V39 controller test
  could not run in this sparse checkout because `doom_hud_signal_v1.py` was not
  materialized.

## Result

The exact-source baseline regression failed all ten malformed counter/rate
cases:

- `10.5 → 11.5` is reduced to integer bounds `10 → 11`;
- `True → 2` is reduced to integer bounds `1 → 2`;
- `10 → 10.5` is reduced to `10 → 10` and incorrectly appears stable.

The candidate requires exact nonnegative `int` values for episode tics and
kill/death counters, a positive exact `int` tic rate, and exact `bool`
terminal flags. The five focused tests pass in normal and optimized Python.
Existing V15 lifecycle/selection coverage previously passed 8/8 with an inert
`executor_v13` import stub; the sparse checkout omitted runtime modules, so
this does not qualify full runtime startup.

## Reproduction

From the repository root:

```powershell
python -B -m unittest research.doom.test_session_map01_v15_ticks -v
python -B -O -m unittest research.doom.test_session_map01_v15_ticks -v
python -B -m py_compile research/doom/session_map01_v15.py research/doom/test_session_map01_v15_ticks.py
python -B research/doom/v15_scorer_tick_guard_a01_20261005/audit.py
git diff --check
```

The fix is on a branch based on PR #7843's head. It should be reviewed with
that opt-in session change. It does not authorize or spend a live allocation.
