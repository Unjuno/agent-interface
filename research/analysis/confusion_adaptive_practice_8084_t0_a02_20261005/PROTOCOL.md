# Issue #8084 — T0 method-readiness allocation A02

## H / T / D / C / U

**H.** For the six frozen synthetic confusion matrices, the pre-outcome span/peak gate activates exact pair-focused interleaving only on eligible heterogeneous cases; otherwise the adaptive arm equals the seeded neutral schedule. An independent scorer labels all four frozen effect traces correctly.

**T.** Six matrices (three high-heterogeneity pair patterns, uniform, low-dispersion, threshold-boundary); three practice variants; four attempts per variant; max identical run two. Candidate-visible input is only `candidate.py` and `cases.json`; it receives no held-out IDs, expected effects, or scoring fixture. Candidate and auditor are separate, once-only OrbStack invocations using the pinned Python digest and network-disabled, read-only root filesystems. Auditor receives the hidden scorer fixture read-only and independently reconstructs equal exposure, adaptive pair-optimal schedule, neutral fallback, held-out exclusion and scoring. Mutation tests alter held-out exposure, quota, gate label, and optimizer result.

**D.** `METHOD_PASS_SCOPED` requires zero independent audit errors across six cases/12 schedules, exact four-per-variant exposure, streak cap, maximum pair adjacency under constraints, exact fallback on all ineligible cases, no held-out IDs in any practice schedule, and expected scorer labels. Otherwise retain `HOLD_METHOD_GATE`; no human-effect claim at T0.

**C.** This authored generator places an explicit strong pair signal in three cases, making pair-focused scheduling easy by construction; seeded neutral schedules sometimes already emphasize that pair. Thresholds are stipulated, not calibrated.

**U.** Synthetic method readiness only. No participants, learning, retention, delayed transfer, real confusion reliability, safety, accessibility, GUI, product, or runtime effect. Any T1 requires separate consent/privacy/ethics review and fresh coordination with #8080.

## Frozen fixture and input isolation

`cases.json` contains only practice variants and confusion matrices. Held-out IDs and effect truth exist only in `scoring_cases.json`, mounted only into the auditor container. Each schedule has 12 practice slots. Eligibility is `span >= 0.25 AND peak >= 0.70`. Pair order is AB, AC, BC; ties resolve in that order. The optimizer maximizes target-pair adjacency subject to exact quotas and a two-item streak cap, then uses lexical sequence tie-breaking.

