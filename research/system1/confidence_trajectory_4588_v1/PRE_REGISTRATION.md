# Confidence-trajectory Local System-1 synthetic experiment (Issue #4588)

Allocation `confidence-trajectory-system1-v1`; branch `research/confidence-trajectory-4588-v1-20260927`; additive path `research/system1/confidence_trajectory_4588_v1/`.

## Question and bounds

Compare current confidence only against causal velocity, acceleration, and causal-smoothed trajectory features for a four-way `ACTION_A` / `ACTION_B` / `NO_OP` / `YIELD` decision. All arms use the same linear classifier shape, initialization, optimizer, train/test rows, feature normalization and step schedule; only registered feature masks differ. No confidence or history grants execution authority.

Ten seeds: `2026100100` through `2026101000` in 100-point increments. Each seed creates stratified train and held-out temporal examples from ten frozen families. No replacement seeds, retries, post-result tuning, or pooling with other Issues. Per-seed arm model states, logits, predictions, raw inputs, labels, family/alias identifiers, training schedule, timings and hashes are retained.

## Decision contract

Before training, source, data generator, splits, feature masks, optimizer, number of steps, thresholds, Docker image ID, and independent auditor are frozen. A scoped PASS requires the registered trajectory arm to reduce false-executable rate by at least 20% relative and 2 percentage points absolute on the exact acceleration-alias held-out subset versus CURRENT_ONLY; preserve total actionable/NO_OP accuracy within 2 percentage points; not increase overall false-executable rate; reduce unnecessary action on NO_OP rows by at least 10 percentage points without false NO_OP on required-action rows; produce YIELD for every stale/missing/epoch-invalid row; and retain the benefit on noisy/irregular samples. The acceleration arm must improve alias accuracy by 5 points over velocity; otherwise acceleration is rejected as unnecessary. Report every denominator, arm and seed even on FAIL/HOLD.

## Safety and runtime

Cached `needle-pilot05:local` only; CPU, one torch thread, no network, read-only root and source, dedicated output mount, bounded CPU/memory/PIDs. No packages, image pulls, GUI, input dispatch, user data, provider/network calls, runtime authority, or product promotion. Exactly one formal orchestration and zero retries. Any source/hash/image/protocol/evidence failure is a typed STOP/HOLD, not a model result.

## Limits

Synthetic temporal confidence only. No real perception calibration, cross-app transfer, task success, live action safety, human tempo, or general Local System-1 claim.

