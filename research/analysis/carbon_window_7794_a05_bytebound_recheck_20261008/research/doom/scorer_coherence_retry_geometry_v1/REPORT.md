# Scorer coherence retry geometry v1

Issue: #944  
BASE: `d303c98522c47cb35d0db511e05d26d29e91d85b`  
Formal deterministic invocations: **1**  
Reruns/tuning: **0**  
Decision: **`HOLD_GRID_TOO_COARSE`**

## Result

The primary three-attempt geometry behaved exactly as hypothesized in both independent implementations:

- 35 Hz period: `T = 28,571,429 ns`;
- phase-independent three-attempt bound: `floor(2T/3) = 19,047,619 ns` = **19.047619 ms**;
- 10 ms, 18 ms and 19.047619 ms produced no all-three-failure phase;
- 19.048620 ms produced a nonempty failure interval of **3,002 ns**, with the 1 us phase grid finding three failing phases;
- 20 ms produced `2,857,142 ns` of failing phase measure, approximately **10%** of one tic;
- 25 ms produced `17,857,142 ns`, approximately **62.5%**;
- one full tic produced failure for every phase.

For the frozen spans above the three-attempt boundary, the independent interval construction gives the descriptive relation `failure_measure = 3d - 2T` within this modeled regime. This is an interpretation of the retained rows, not an additional execution.

## Why the formal disposition is HOLD, not PASS

The frozen two-attempt negative control intentionally tested `floor(T/2)+1 ns = 14,285,715 ns`. The interval method found a real all-two-failure interval of exactly **1 ns**: `[28,571,428, 28,571,429)`. The separately frozen 1 us phase grid cannot sample a 1 ns interval and therefore reported no failing grid point.

The issue preregistered this exact possibility as `HOLD_GRID_TOO_COARSE`. The experiment is therefore retained as HOLD even though:

- scientific-integrity errors are `[]`;
- the primary three-attempt rows agree between interval and grid methods;
- the exact three-attempt boundary is supported by the first outcome.

Do not rerun at a finer grid under this allocation to convert HOLD into PASS.

## Implication for MAP01 measurement integration v2

Under the idealized assumptions of this experiment—perfectly periodic 35 Hz tics, constant bracket span, immediate retries and no additional inter-attempt delay—the current three-attempt scorer has a useful diagnostic boundary:

> a per-attempt bracket span at or below about **19.05 ms** is phase-independent in this model; above it, phase alone can exhaust all three attempts.

This does **not** establish that live ViZDoom spans are below that value. It also does not justify changing `session_map01_v13.py`, increasing retry count, or changing the frozen `map01-measurement-integration-live-02` allocation. Real API duration variability, Python scheduling, capture load and non-periodic effects remain unobserved.

## Retained integrity

Container source/result SHA-256:

- `PLAN.md`: `2167bb460e7de39d0935e0f0c79ab06838381b9c58973aace3d0f561a02e48e4`
- `geometry.py`: `06823aa1ecd41c16ed1fb5b6cdf5feb56a8f1049d6c9e0cb76e576f061a4cfe6`
- `run.py`: `f67ee9c1041101d9ec97b95a9b10fc5dd7348e7660b391cb8376fc3831a20808`
- `audit.py`: `608dd1e6aee018d401ffd3232703376f68fb128620a8986f0fbbff9b60a9b773`
- `result.json`: `4f0ff2113f79b1703a62a534b72688cddfdf52a17eb67b7c9d9b0a288bd73289`
- `audit.json`: `513ad0bf1daaf739f32b9cf83a68edebaf2425fd9dc3a2c83c14ce928716db9a`

No ViZDoom, X11, model, provider or task input occurred.
