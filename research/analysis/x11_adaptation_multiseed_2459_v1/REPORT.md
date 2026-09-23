# X11 shift adaptation multiseed reproducibility

## H/T/D/C/U

- H: bounded X11 shift adaptation remains useful across random seeds without accepted false positives.
- T: fixed split: base 160 + first old-shift 80 train, final old-shift 80 held out; same 354-parameter CNN; seeds 2401–2405.
- D: existing source-bound X11 raw frames/manifests; evaluation frames unchanged; CUDA RTX 3080.
- C: reproducibility only; no fresh-family generalization, semantic/runtime/token/latency/gameplay claim.
- U: seed sensitivity and calibration remain unresolved; accepted false positive is FAIL.

## Result

| seed | accuracy | accept | YIELD | false positive |
|---:|---:|---:|---:|---:|
| 2401 | 91.25% | 15 | 65 | 0 |
| 2402 | 90.00% | 17 | 23 | 0 |
| 2403 | 91.25% | 14 | 66 | 0 |
| 2404 | 80.00% | 9 | 71 | 0 |
| 2405 | 83.75% | 15 | 25 | 0 |

Mean / minimum accuracy: **87.25% / 80.00%**. Aggregate false positives: **0**. The single-run 88.75% is not promoted as representative; utility is seed-sensitive.
