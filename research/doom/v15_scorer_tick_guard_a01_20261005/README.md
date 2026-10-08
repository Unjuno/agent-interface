# V15 scorer input-integrity guard A01

This follow-up repairs a source-contract gap in the opt-in V39 measurement
session from PR #7843. That session selects `session_map01_v15.py`; its scorer
used `int(...)` for episode tics, progress counters, and tic rate. Boolean or
fractional values could therefore be silently converted into plausible score
inputs, and invalid rates could contaminate timeout fallback calculations.
ViZDoom documents `get_game_variable` as returning a Python `float`, so valid
integral floats must remain supported by the scorer.

## H / T / D / C / U

- **H:** Exact selected V15 scorer code accepts Boolean/fractional/negative
  counters and tic rates by coercing them with `int(...)`; a strict-int repair
  would reject documented integral-float counter values.
- **T:** AST-isolated regression against the exact selected V15 source. Reject
  malformed tic, kill/death, and terminal-flag values; preserve exact controls.
  No game, model, GUI, display, or OS input is initialized.
- **D:** The baseline fails malformed-input checks. Candidate passes focused
  tests in normal and optimized Python, including documented integral-float
  counters.
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

The candidate requires exact nonnegative `int` values for episode tics, finite
nonnegative integral-valued kill/death numbers (including ViZDoom's documented
float), a positive exact `int` tic rate, and exact `bool` terminal flags. The
ten focused tests pass in normal and optimized Python. The V15 lifecycle/
selection suite passes 8/8 with an inert `executor_v13` import stub against
this candidate. This does not qualify full runtime startup or the end-to-end
V39 controller path.

## Reproduction

From the repository root:

```powershell
python -B -m unittest research.doom.test_session_map01_v15_ticks -v
python -B -O -m unittest research.doom.test_session_map01_v15_ticks -v
python -B -m py_compile research/doom/session_map01_v15.py research/doom/test_session_map01_v15_ticks.py
python -B research/doom/v15_scorer_tick_guard_a01_20261005/audit.py
git diff --check
```

The exact normal and optimized unittest outputs are retained as
`tests-normal.log` and `tests-optimized.log`; the lifecycle/selection output is
`tests-lifecycle-selection.log`. `RESULT.json` records their SHA-256 digests,
and `audit.py` verifies all three logs alongside the candidate source/test
hashes.

## Contract correction

The first follow-up revision overconstrained kill/death values to exact Python
ints. The official ViZDoom API specifies `get_game_variable(...) -> float`, so
an integral-float control exposed that the candidate rejected a valid API
value. This correction was test-first: the integral-float test failed with
`ValueError: invalid kill count`, then passed after finite/integral validation
was added. Fractional, Boolean, nonfinite, and negative counter controls still
reject. No ViZDoom process was started to make this correction.

The fix is on a branch based on PR #7843's head. It does not authorize or spend
a live allocation.


## Optional timeout method contract

When `is_episode_timeout_reached` exists, V15 now requires the attribute to be callable and its return value to have exact type `bool`. Malformed integers, floats, strings, and `None` reject before the scorer can report success. The tic-derived timeout fallback applies only when the method attribute is absent. The expanded isolated suite checks malformed values, both valid Boolean outcomes, a non-callable attribute, and the absent-method fallback.
