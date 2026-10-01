# Follow-up: target drift, ROI margin, and exact identity search

Status: development evidence only. Same research branch/base as `REPORT.md`.

## Failure added

Only one new failure was added to the retained 48x48 scoped detector: horizontal displacement of the relevant 12x12 visual change relative to the declared ROI. Synthetic rendering jitter remained sigma=2, effect delta=16, fixed pixel threshold=12 and changed-fraction threshold=5%, 1,500 trials/offset.

| target center drift | hit rate | median changed pixels in ROI |
|---:|---:|---:|
| 0-18 px | 100% | 136 |
| 19 px | 99.87% | 125 |
| 20 px | 20.67% | 114 |
| 21 px | 0% | 102 |
| 22 px | 0% | 91 |
| 24 px | 0% | 68 |
| 28 px | 0% | 23 |
| 32 px | 0% | 0 |

The retained tight scope therefore has a sharp spatial validity boundary. A narrow ROI must be treated as expiring spatial evidence, not as a permanent target identity.

## Competing repair: enlarge the ROI

The next ablation changed only ROI extent and used an absolute threshold of 100 changed pixels. Relevant target drift was fixed at +24 px. A same-sized irrelevant patch was placed at +32 px.

| ROI | no-change hit | drifted target hit | nuisance-margin hit |
|---:|---:|---:|---:|
| 48 | 0% | 0% | 0% |
| 64 | 0% | 100% | 0% at +32 px |
| 80 | 0% | 100% | **100%** |
| 96 | 0% | 100% | **100%** |

The apparent 64x64 sweet spot was not general. Holding ROI=64 and moving the same nuisance closer gave 100% nuisance hits through center offset 28 px, 85.5% at 29 px, and 0% from 30 px outward (1,000 trials/offset). Therefore simple margin enlargement only moves the boundary between target recovery and irrelevant-change sensitivity.

## Existing mechanism check

Current main already has `research/live_control/scoped_target_handle_v1.py`. Its `TargetHandleStore` supports bounded `search_radius`, `local_translation`, `MOVED`, `AMBIGUOUS`, `MISSING`, and `REVALIDATED` outcomes. Its search contract is exact-region bytes: candidate crops are compared byte-for-byte with the minted patch.

A microbenchmark of that exact-search core using the same PIL crop/tobytes operation on a 140x100 image with an 8x8 unique patch produced:

| search radius | nominal candidate positions | median search time | p95 |
|---:|---:|---:|---:|
| 0 | 1 | 4.4 us | 6.4 us |
| 6 | 169 | 0.653 ms | 0.818 ms |
| 12 | 625 | 2.408 ms | 2.748 ms |
| 24 | 2,401 | 9.556 ms | 10.782 ms |
| 48 | 9,409 | 36.217 ms | 38.275 ms |
| 64 | 16,641 nominal* | 45.954 ms | 49.698 ms |

`*` actual candidates are clipped by image bounds.

Contract probes in the same microbenchmark behaved as expected for exact identity: stable=one match; +6 px move within radius=one match; duplicate identical patch=two matches/ambiguous; changing only one source-patch channel by +1 produced zero exact matches.

This is not a benchmark of the full imported `TargetHandleStore`; it isolates the exact nested crop/byte-compare core already visible in that implementation.

## Interpretation

Do **not** replace scoped invalidation with exact target-handle search at frame cadence. The two mechanisms answer different questions:

- high-rate scoped change detector: "did the policy-relevant visual region materially change?"
- low-rate exact handle revalidation: "is this exact previously-grounded identity still uniquely present within a bounded displacement?"

At the measured medians, running radius-12 exact search at 120 Hz would consume about 289 ms of search wall time per second (~29% of one-core time if serialized and CPU-bound), versus ~0.535 ms/s for the 4.457 us scoped detector. These are arithmetic compute-share proxies, not measured process CPU utilization.

## Candidate direction

**Two-timescale local evidence:**

1. sample a planner/policy-declared ROI at high cadence with a cheap robust invalidation predicate;
2. on a bounded renewal/yield/revalidation boundary, use the existing target-handle identity mechanism at a small search radius;
3. continue locally only on a unique permitted `REVALIDATED` identity; yield on ambiguity/missing/stale/scope mismatch;
4. do not enlarge the high-rate ROI indefinitely to compensate for target motion.

## H / T / D / C / U

**H:** separating high-rate change detection from low-rate identity revalidation can preserve fast invalidation while avoiding both large-ROI nuisance sensitivity and per-frame exact-search cost.

**T:** target drift only, then ROI margin only, then exact-search-core microbenchmark. No model/Doom/formal allocation.

**D:** target drift falsified permanent validity of the tight ROI. ROI enlargement alone is **REJECTED as a general repair**. Two-timescale composition is **HOLD / next candidate**, not yet promoted.

**C:** exact-pixel identity may fail under benign rendering changes; the revalidation step may therefore yield too often. Conversely, tolerant matching could create false identity and weaken safety.

**U:** the exact-search timing is a core-operation microbenchmark, not the imported runtime class; no live moving GUI target; no compositor/GPU; no model boundary; no OS input.

## Next smallest experiment

Use the actual current `TargetHandleStore` on one live X11 moving target with a frozen small search radius. Compare only: (A) immediate yield on scoped visual change; (B) one bounded exact revalidation attempt after the same change. Seed an exact move, a one-pixel rendering perturbation, and a duplicate patch. Measure resolution status, added latency, and avoided planner-yield count. Do not introduce tolerant matching unless exact revalidation first fails on a benign case that matters.
