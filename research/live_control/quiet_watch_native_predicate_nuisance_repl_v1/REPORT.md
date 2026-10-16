# Native-predicate nuisance-only scheduling replication

Task `QUIET-WATCH-NATIVE-PREDICATE-NUISANCE-REPL-20260916-001`, Issue #283.

**Disposition: `REPLICATE_STABLE_SCOPED`.** This is a replication/stability result for the scoped synthetic X11 watcher only. It does not promote shared runtime code, establish hard-real-time behavior, or show an end-to-end agent improvement.

## Question

Issue #270 passed its live integration gate but the median max-gap ratio was 1.0979 against a 1.10 gate, with two of four nuisance pairs individually worse than 1.10. This successor keeps the same native XGetImage acquisition and Python-vs-native exact-count intervention, but uses a larger nuisance-only matched block to test scheduling-gap stability without adding a new mechanism.

## Frozen design

- publication base: `3c6f07f0660aee854d6b2d2d0f525fd9f451de68`
- frozen branch head before formal: `c24ad06a2740bdcb0152a741df1a9fbdb4693d8d`
- 12 matched nuisance pairs / 24 live cases
- nominal 2 ms cadence, 600 ms owner deadline
- identical 32x32 ROI and native XGetImage path
- only intervention: Python exact BGRX count vs native exact BGRX count
- first outcomes only; no formal retry, replacement or extension
- stability gate chosen before data: median max-gap ratio <=1.10 and >=8/12 pairs individually <=1.10
- cost gates retained: median CPU ratio <=0.80; median wall ratio <=0.90

The first source publication attempt exposed a byte mismatch between local and GitHub `run.py` before any formal case. The freeze was corrected and preregistration rebound; Git blob identity was verified before formal execution. The excluded two-case preflight then remained construction-only.

## Formal first outcome

| endpoint | result | frozen gate |
|---|---:|---:|
| false nuisance cancels | 0/24 | 0 |
| release/integrity | 24/24 pass | all pass |
| median paired CPU ratio | 0.308610 | <=0.80 |
| median paired wall ratio | 0.515988 | <=0.90 |
| median paired max-gap ratio | 0.996468 | <=1.10 |
| pairs with gap ratio <=1.10 | 9/12 | >=8/12 |

Decision: **`REPLICATE_STABLE_SCOPED`**.

The candidate preserved the large observation-path CPU/wall reduction and the preregistered gap-stability criterion replicated. However, this is not a tail-latency win: three pairs exceeded 1.10, with ratios 1.626, 1.519, 1.377. One candidate case sampled 300 rather than 302 times and had a 4.226 ms max gap. The correct interpretation is that the *median/bounded replication criterion* passed while scheduler tails remain variable.

## Audit

Independent audit reclassified 7,270 retained ROI payloads, checked digest/count identity, exact schedule/source/binary binding, release integrity, timestamp ordering, xz round-trip, and recomputed every summary ratio/decision. Four negative mutations (pixel count, source identity, release receipt, timestamp order) were all rejected.

- raw JSON SHA-256: `a6bba56f493ba23a1c896b764019c7ee7136ec2d3356af2b6b4a7b1ee95488da`
- raw xz SHA-256: `80d19bb11f2ec828202459dce388a2de0fd51dc38e462888b2e3f8e40e280e9f`

## Limits / next rung

One Xvfb host, unpinned CPU frequency, Tk scheduling, X-server latency and OS scheduling remain confounds. The next useful rung is **not** another optimization. Because 3/12 pairs still show >10% max-gap regression, the next discriminator should isolate whether those tails arise during XGetImage service time, Python/Tk main-loop contention, or host scheduling, while keeping the mechanism fixed.
