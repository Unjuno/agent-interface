# CPU placement and 2 ms wake tails

Task `QUIET-WATCH-CPU-PLACEMENT-20260916-001`, Issue #330.
Publication BASE `c6d195473be0aa876cc991093262494209c7971f`.
Pre-measurement source HEAD `ee524ad9cfd6ba73be07c96ef3e5d67e5787e0d9`.

**Decision: `CPU_PLACEMENT_EFFECT_SCOPED`.** Moving the identical busy child from the observer's guest logical CPU to another guest-reported core reduced the median paired block-maximum wake lateness under the frozen gate. This does NOT give a worst-case bound: the other-CPU arm had the largest observed spike, 10.033039 ms. No shared runtime change is proposed.

## Why this step

#316 / #320 isolated same-CPU contention without X11, Tk or a predicate. This successor adds the missing placement control, rather than rerunning that allocation or modifying scheduling priority. #283's duplicate-allocation invalidation remains intact. Intake checked main, visible branches and matching issues; this new ID was consumed once by this session.

The earlier loop processes overdue absolute deadlines in catch-up fashion; it does not skip slots. We preserve that behavior. The recorded `overdue_deadlines` counts sampled deadlines at least one period late, NOT independent lost visual events or distinct missed observations.

## Frozen design and actual environment

Twelve matched triplets, arms `idle` (no child), `same` (busy child on observer CPU), and `other` (same busy child on another guest core). All six permutations occur twice. Each arm has 300 deadlines at a 2 ms period, 30 ms settling, and the inherited 10 ms initial lead-in. Consequently the planned span from block start to last due time is 608 ms, not an asserted exact 600 ms wall duration. There are 36 blocks and 10,800 exact timestamp triples. They are correlated repeated measurements, not 10,800 independent replications.

Only child placement differs between the two loaded arms. The loop, Python interpreter, load instructions, sample count, clocks, priority and result handling stay the same. Child readiness, affinity, CPU-time progress, liveness and termination are checked. Results are journaled between blocks. No GUI, X11, input authority, model or game is exercised.

CPython 3.13.5; Linux 6.18.44 x86_64 / glibc 2.41. The guest reports AMD EPYC 9V74, approximately 2.596 GHz at inspection, frequency unpinned. Initial allowed CPUs are 0..4. The observer uses CPU0; the other arm uses CPU1. Guest topology reports different cores in package0 and one thread per reported core. **Physical host CPU mapping is UNKNOWN.** This is not verified physical-core isolation. SCHED_OTHER / nice0 is unchanged. The cgroup quota is 400000/100000, four CPU-equivalents. Batch size is one timing loop; blocks run serially. Raw environment and per-block cgroup metadata are retained.

## H / T / D / C / U

**H:** separating the busy child lowers maximum wake lateness relative to same-CPU competition.

**T:** the source-first 12-triplet block above, one outcome per scheduled arm, no retry, replacement or extension. One unscored three-arm construction preflight preceded measurement. Timing from preflight was not used to tune gates.

**D:** require all source/schedule/arithmetic/child integrity checks, median paired other/same maximum-lateness ratio <=0.50, at least 8/12 individual ratios <=0.50, and same-CPU median maximum >=1 ms. Otherwise HOLD, or FAIL on integrity error. Idle and p99 are descriptive, not alternative routes to PASS.

**C:** CPU placement changes dispatch competition but can also interact with guest/host scheduling, cache, frequency and background activity. A synthetic stationary busy loop differs from X11/Tk work. No cause is assigned to an individual spike.

**U:** one VM, one selected guest CPU pair, fixed balanced rather than randomized order, finite serial allocation, uncalibrated host clock and nonstationary scheduling. No calibrated combined standard uncertainty or coverage factor is assigned. Ranges are observed ranges, not confidence intervals. No physical-core, hard-real-time, live detection, input-release or product latency claim follows.

## First result

| Per-block statistic, median across 12 blocks | Idle | Same CPU | Other CPU |
|---|---:|---:|---:|
| Maximum wake lateness, ms | 0.221518 | 2.230225 | 0.163901 |
| p99 wake lateness, ms | 0.106057 | 0.312195 | 0.124288 |
| Block-max observed range, ms | 0.113512..1.749050 | 0.209450..3.552015 | 0.120751..10.033039 |

Primary median of paired other/same maximum-lateness ratios: **0.1444794839184006**. Qualifying pairs: **8/12**, exactly the frozen minimum. Same-CPU median maximum: **2.2302245 ms**. All integrity gates pass. Do not confuse the median of paired ratios with the ratio of marginal medians.

Three pairs worsen under other-CPU placement: triplets 0, 1 and 3 have maxima 3.659085, 6.945668 and 10.033039 ms. A fourth pair improves by less than 50%. Thus the aggregate gate passes but placement does not eliminate long tails. The median per-block p99 is also not the pooled p99.

All 36 measured cgroup snapshots have zero increment in `nr_throttled`. Both loaded arms advance 60..61 child CPU ticks per block with SC_CLK_TCK=100. This checks workload presence and observed cgroup throttling, not all host interference. Affinity, child liveness and SIGTERM cleanup checks pass in every applicable case.

### Metric definitions and unit check

| Field | Meaning | SI unit / stored unit | Domain / type |
|---|---|---|---|
| due | Scheduled monotonic deadline | s / integer ns | Nonnegative integer scalar |
| wake | Timestamp after wait or catch-up | s / integer ns | Integer scalar, no earlier than due |
| late | wake minus due | s / integer ns | Nonnegative integer scalar |
| block maximum | Largest late in one 300-deadline block | s / ns | Nonnegative scalar |
| other/same ratio | Corresponding block maxima divided, denominator floored at 1 ns | 1 | Nonnegative real scalar |

Subtracting two timestamps gives a duration. Dividing two durations gives a dimensionless ratio. Reporting nanoseconds in milliseconds divides by 1,000,000; no nominal-period substitution is used for observed lateness.

## Audit, retention and deviations

The independent `audit.py` was frozen before scored measurement and imports no measurement code. Fifteen synthetic mutations were rejected before measurement, covering 1 ns timestamp errors, types, sample/block count, chronology, order, affinities, dead/no-progress child, cleanup, source identity and transport corruption. A HOLD fixture and exact codec round-trip also pass. The frozen audit passes the actual raw; no post-formal audit repair was needed. `verify.py` is an additive offline publication checker, not a changed experimental gate.

The construction preflight predates added cross-block audit/test checks; its initial source-hash snapshot and raw remain in the downloadable bundle, not relabeled as the final freeze. An exception-type typo in an uncommitted source-transfer tree was corrected before source commit. During raw transfer, three corrupted transcription attempts were rejected by Git blob identity and never linked into the published tree.

An outer 40-second command timeout occurred after the runner wrote all 36 blocks and the independent audit wrote its summary, at the offline compression stage. Only offline packing/unpacking resumed; the measured allocation was NOT rerun.

**Full formal retention:** canonical raw JSON is 407,014 bytes, SHA-256 `b55029b42ee9ed9565fa3e2e04b8793d64fad4d63bb6587206d384ffca7f6cd1`. Lossless delta-varint plus zlib transport is 30,098 bytes before outer Base64, SHA-256 `a7af99533596bea2a86ddb90925ed9cc08f19caad3ecc38376a97bbfcad9bb1a`. All 10,800 due/wake/late triples reconstruct exactly. The ten text chunk blob IDs were checked against local Git hashes. Reconstruction from the byte-identical publication files and a separate-directory offline audit pass. No claim is made to having downloaded the complete archive through container networking.

From this directory, verification is offline only:

```sh
python verify.py
python test_audit.py
TMPDIR=$(mktemp -d)
python codec.py unpack raw "$TMPDIR/raw.json"
python audit.py "$TMPDIR/raw.json"
```

Do not rerun `run.py measure` under this consumed task ID. A new performance allocation requires a new identity, new source freeze and coordination check.

## Next single question

Does the same guest-CPU placement intervention improve actual cue detection or input-release timing when composed into the fixed native live watcher, without changing its predicate, cadence or authority deadline? Keep scheduling priority unchanged; this scheduler-only PASS is not an integration result.
