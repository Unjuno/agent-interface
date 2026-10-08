# Issue #5870 T0 report — online rent-or-compile boundary

## Result

**`FAIL_ONLINE_VALUE_PURE_CASE` for the preregistered cumulative-regret hypothesis.** On all four qualified positive-saving configurations, the frozen horizon-blind `RENT_THEN_COMPILE_CUMULATIVE_PREMIUM_V1` policy beat `DIRECT_ALWAYS` but did **not** strictly beat `COMPILE_IMMEDIATELY` on worst-prefix cumulative regret. It was worse in every such configuration. The one unqualified case and one case without per-use savings remained direct-only as required.

The independent auditor reconstructed all 180 use rows across six configurations and 30 prefixes each with zero errors. All four corruption controls rejected: omitted event, false unit charge, compile without qualification, and injected future-horizon field. The candidate subprocess ran once and exited 0. The separate auditor subprocess ran once and exited 0 with scientific status `FAIL_ONLINE_VALUE_PURE_CASE`; an audited negative result is not an execution STOP.

| Config | Direct / setup / guarded | Eligibility | Rent worst regret | Direct worst regret | Compile-now worst regret |
|---|---:|---|---:|---:|---:|
| a | 10 / 30 / 4 | qualified, positive saving | 30 | 150 | 24 |
| b | 10 / 30 / 7 | qualified, positive saving | 30 | 60 | 27 |
| c | 7 / 20 / 3 | qualified, positive saving | 20 | 100 | 16 |
| d | 5 / 11 / 3 | qualified, positive saving | 12 | 49 | 9 |
| e | 6 / 10 / 8 | qualified, no saving | 0 | 0 | 70 |
| f | 10 / 30 / 4 | unqualified | 150 | 150 | 24 |

The observed pattern is scoped to this frozen cost grid and policy: for each positive-saving configuration, rent-then-compile's worst regret equals the setup charge, while compile-immediately's worst regret is lower by the per-use saving. Rent-then-compile still reduces regret relative to direct-always on these recurrent horizons. This rejects the stronger preregistered claim that it strictly improves on **both** simple baselines; it does not show that all online policies fail or that the compiled route lacks value.

## Frozen execution

- Main base: `da7770df8bd896738a8a7e0ccc8ea45e10b3e645`.
- Freeze commit: `f0abf4948757f080cbad5de009bec5f8927da9b7`.
- Candidate: `python -B candidate.py`, once, exit 0; stdout and raw SHA-256 are in `RUN.json`.
- Auditor: `python -B audit.py raw.jsonl`, once, exit 0; audit errors 0, controls 4/4 rejected.
- Raw file: 181 JSONL rows including the bound header, SHA-256 `4e1930fdafb5be5fe4592482927df65efa822911b56f450bac778b2d768719ed`.
- Independent audit: `audit.json`, SHA-256 `bd4de3772962d11232066077e92a509e0522a0fe7807e0508d5325a6e79366c2`.
- Construction/local checks: 5/5 standard-library tests passed before freeze and again after the formal run; AST and JSON syntax checks passed.
- Host: Windows 11 Home 10.0.26200, CPython 3.12.10. Docker Desktop CLI was installed, but its service was stopped/manual and Engine lookup timed out; no container was run or inspected. No model, GUI, user input, GPU, network, or external effect was used.

## Limits / next question

This is an exact finite arithmetic result over six authored configurations and the declared regret metric. It does not measure real compilation, validation, direct or guarded route cost; future task demand; randomization; invalidation; repair; correctness drift; shared cache state; or user benefit. In particular, it does not establish a classical competitive guarantee or transfer any ratio/regret conclusion to live Agent Interface methods. The invalidation and costly-repair cases in #5870 remain untested. Keep Issue #5870 open for a separately preregistered follow-up that either optimizes a distinct regret objective or adds the invalidation-aware lifecycle without changing this result.

