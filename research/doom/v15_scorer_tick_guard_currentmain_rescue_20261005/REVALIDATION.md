# Issue #59 / #7852 V15 scorer tick guard — current-main rescue

## H — Hypothesis

The V15 scorer should reject malformed episode-tick, counter, tic-rate, terminal, and timeout values instead of coercing them into plausible progress or success data, while still accepting finite integral-float kill/death values.

## T — Current-main checks

- Applied the focused #7852 patch to `session_map01_v15.py` on current `main` `e724d6d795da2852c043cb53cfd92d5a9222a091`; three-way application was clean. The resulting source change is limited to `_coherent_progress_sample` plus `math` import; original #7852 and #7843 branches remain untouched.
- `python3.12 -m unittest -v research.doom.test_session_map01_v15_ticks`: 10/10 passed.
- `python3.12 -O -m unittest -v research.doom.test_session_map01_v15_ticks`: 10/10 passed.
- `py_compile` for scorer and focused test: passed.
- The regression rejects bool/fractional/negative tics and rates, malformed/nonfinite counters, non-bool terminal/timeout values, and non-callable timeout attributes; accepts integral-float counters; and checks absent-timeout fallback.

## D — Data and scope

Retains the original #7852 frozen result, exact logs, and audit package unchanged, plus this additive current-main revalidation note. These are host-side AST-isolated tests over the exact selected scorer function. No ViZDoom process, game, model, GUI, display, OS input, live allocation, or end-to-end V39/V15 controller run occurred. The recorded lifecycle/selection result is historical and was not rerun in this composition.

## C — Conclusion

PASS for the narrow V15 scorer input-type contract on this current-main composition. Not a live API-return-type, integrated controller, useful-feedback, task-success, or safety result. Kept draft pending independent review.

## U — Remaining uncertainty

ViZDoom's actual return values and full V39/V15 composition are unverified here. Existing review feedback on #7852 requested direct post-sample Boolean coverage and exact timeout-result validation; the current patch contains both and the focused tests exercise them, but this successor still needs nonauthor review and repository policy checks before integration.
