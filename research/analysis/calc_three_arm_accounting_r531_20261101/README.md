# Recount of archived three-arm Calc comparisons

This is a read-only re-audit of existing evidence at main `ac67f9420e4524d555b8d6b5f3cb99efeba3b01a`; it is not a new live run. The two archived comparison programs re-audited all 12 saved attempts, including saved-cell and neutral-input checks, distinct owner sessions and model-call IDs, and per-route input hashes. `recount.py` adds launcher-interval medians and relative figures without altering the underlying trials. `recount.json` is the saved output.

**Archive metadata discrepancy discovered in a later review:** all six fixed-block `conditions.json` files list `values` and pass criteria as 472/615 but also contain an `intervention` sentence referring to 641/283. The retained input code and independent saved-file scoring checked by the archived auditor use 472/615. The conflicting sentence is preserved; it leaves ambiguity in the documented intervention and is not silently corrected. See [PROFILE.md](PROFILE.md).

| Workload | Route | Samples | Task median | Launcher median | Input-token median |
|---|---|---:|---:|---:|---:|
| Fixed | direct | 2 | 6.258 s | 9.922 s | 12,185 |
| Fixed | compiled | 2 | 6.561 s | 8.930 s | 12,185 |
| Fixed | fresh | 2 | 9.659 s | 13.375 s | 25,743 |
| Temporary obstruction | direct | 2 | 9.278 s | 12.961 s | 25,751 |
| Temporary obstruction | compiled | 2 | 10.150 s | 12.476 s | 25,751 |
| Temporary obstruction | fresh | 2 | 12.096 s | 15.813 s | 40,666 |

For these samples, compiled versus fresh had task-median reductions of 32.1% fixed and 16.1% with temporary obstruction; input-token median reductions were 52.7% and 36.7%, respectively. The direct task median was lower than compiled in both blocks. The percentages compare medians of only two observations, not individual paired speedups or confidence intervals. Cached input is included in input totals, not added again.

Task time excludes startup, fixture preparation and audit; launcher time includes launched-process startup but still excludes fixture preparation and audit. No all-in cost or completion latency is established. The fixed layout and known values, expected-value OCR, scripted Save, unequal model calls, different cache/provider conditions and test-created/removed overlay limit interpretation. This does not establish general speed, cost, reliability, persistent-obstruction recovery, partial-input recovery, arbitrary editing, MAP01 or project completion.

Reproduce with normal Python and Pillow, from a checkout containing the four archived directories:

```text
python research/analysis/calc_three_arm_accounting_r531_20261101/recount.py research/integration
```

A sparse checkout must first include those four `research/integration` directories; otherwise the comparison scripts and archives are absent locally.

The source blocks are [fixed forward](../../integration/wslc_calc_three_arm_20261101), [fixed reverse](../../integration/wslc_calc_three_arm_reverse_20261101), [obstruction forward](../../integration/wslc_calc_three_arm_obstruction_20261101), and [obstruction reverse](../../integration/wslc_calc_three_arm_obstruction_reverse_20261101). They contain the underlying archives and their original caveats. Running under `-O` is refused because the archived auditors use assertions.
