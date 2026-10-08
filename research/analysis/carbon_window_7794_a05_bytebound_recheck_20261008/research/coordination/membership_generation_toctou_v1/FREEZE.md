# Source-first freeze

Task: `COORD-MEMBERSHIP-GENERATION-TOCTOU-20260916-015`
Issue: #472
Immutable publication BASE: `bae0c5ecf990605a807f237b899eb758542935c5`

No measured GitHub state transition has run at publication of this freeze.

Frozen source identities:
- policy.py SHA-256 `725dd5c205a6e2e56c7f9c0d4255e354c81d42189655d1465857fff16bf6bbf0`
- plan.json SHA-256 `019fab20311f601e2b2f0119c3d00c379083fb73e2cd67815048361f8f1394b3`

Measured order:
1. split_stable
2. split_race
3. unified_race

Each fixture starts at membership epoch1 {A,B}, exact epoch1 confirmations, generation1.
- split_stable: validate membership; no mutation; update coordination g1->g2 once.
- split_race: validate membership; update membership to epoch2 {A,B,C}; then write precomputed coordination g2 using the still-current coordination-file SHA once.
- unified_race: validate unified state; update unified state to epoch2 {A,B,C}/g1; then attempt precomputed epoch1/g2 using the pre-change unified-file SHA once.

No measured write is retried with a fresh SHA. No alternate merge/lock/token is introduced.
Decision: `PASS_CROSS_FILE_TOCTOU_BOUNDARY_SCOPED` iff stable split advances, split race also advances after membership changed, and unified stale generation update is rejected leaving exact epoch2/g1.
