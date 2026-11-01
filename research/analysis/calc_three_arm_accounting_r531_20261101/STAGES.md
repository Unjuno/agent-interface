# Saved Calc trial stage intervals

This is a re-analysis of the 12 archived trials, not a new live run. Run
`python research/analysis/calc_three_arm_accounting_r531_20261101/stages_saved.py research/integration`
from a checkout with the archived integration directories and their dependencies
materialized. The script invokes each archived block comparator, checks interval
ordering and the audited task duration, and prints the per-trial and median data
in `stages.json`. Normal Python is required because the archived comparators
use assertions. See [README.md](README.md) and [PROFILE.md](PROFILE.md) for
the experiment, source archives, overall timing, and limitations.

All intervals below rely on the archived runner's contract that these markers
use the same trial-host `time.monotonic_ns` clock; that clock is distinct from
the model host's `runner_ns` discussed in PROFILE.md. Each median
contains only two trials. Seconds are rounded here; the JSON retains the raw
computed durations. `method` starts after the initial model request, dependency
check and first guarded click, and ends before final saved-file scoring. Its
contents differ by route: direct performs entry and save; fresh additionally
requests a second model grounding; compiled runs its graph and, after SAFE_YIELD,
performs a separate bounded recovery and save. The intervals therefore are not
equivalent work, and the differences alone cannot establish a causal overhead.

| Block | Route | Pre-method median (s) | Method median (s) | Post-method median (s) |
|---|---|---:|---:|---:|
| Fixed | Direct | 5.526 | 0.729 | 0.003 |
| Fixed | Compiled | 5.456 | 1.102 | 0.002 |
| Fixed | Fresh | 6.038 | 3.617 | 0.003 |
| Temporary obstruction | Direct | 8.556 | 0.720 | 0.002 |
| Temporary obstruction | Compiled | 9.034 | 1.113 | 0.003 |
| Temporary obstruction | Fresh | 8.752 | 3.341 | 0.003 |

For compiled, the nested owner-attempt interval has a median of 0.684 s in
the fixed block and 0.687 s with obstruction; the subsequent recovery interval
has medians of 0.407 s and 0.414 s. Both are inside method, not additional
costs to add to it. The recorded Tesseract subprocess intervals are also nested
inside method; compiled's recorded calls are part of recovery and do not cover
every visual operation. The JSON retains these intervals for inspection rather
than calling them total OCR time or CPU time. There is also method time outside
the owner attempt and recovery. Medians of nested components need not sum to
the median of the enclosing interval.

The tiny samples, fixed inputs and trial ordering limit generalization. The
fixed-block conditions metadata also contains an intervention string referring
to 641/283 while its values and pass condition state 472/615; the executed
runner and saved-file checks support the latter observed values, but the
intended pre-run freeze is not independently established. These measurements
do not establish MAP01 performance, live input release, all-in preparation
cost, or general real-time performance. They identify recovery as an observable
part of this particular compiled path for a future controlled comparison.
