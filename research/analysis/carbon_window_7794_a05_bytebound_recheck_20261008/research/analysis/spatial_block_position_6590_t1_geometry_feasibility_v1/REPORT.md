# #6590 T1 pre-fit geometry feasibility — OrbStack replication

## Result

**`REPLICATION_PASS_WITH_GEOMETRY_HOLD`.** The corrected OrbStack candidate reproduced the previously retained host enumeration byte-for-byte. A separate raw-only auditor independently reconstructed all 551 strict-interior quadrant sites with zero errors. Under the frozen no-near-duplicate rule, eligible center counts are northwest 6, northeast 6, southwest 3 and southeast 3, below the frozen minimum of 8 independent centers in every block. The visual-model T1 was therefore not launched; Issue #6590's model-effect hypothesis remains untested, not refuted.

The eligibility rule requires every 9×9 evaluation target patch to be disjoint from each of the five 9×9 training-support target patches: `max(abs(dx), abs(dy)) >= 9`. Coordinates, not repeated noise rows, are the spatial units. A larger canvas/support redesign or a different near-duplicate definition needs its own prospective freeze before any model fit.

## Allocation history

- Allocation 01 (`...-20261002-01`) stopped before any container creation. Its host runner attempted `freeze["image"]` although the image is frozen at `freeze["environment"]["image"]`; candidate=0, auditor=0, containers=0. The unchanged freeze is at commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd`; exact STOP is [here](results/preflight-01/STOP.json).
- Allocation 02 (`...-20261002-02`) used a separately frozen and statically tested runner. Candidate and auditor each ran once in separate fresh OrbStack containers; retries=0, model fits=0. Both exited 0. Container creation succeeded for both before either was started.

## Environment and provenance

- Image: `unjuno-6590-geometry-preflight:20261002`, config ID `sha256:d4be3c65847d7276752000268bf97c5ea9cb6ce85f93b1ffc9aced409c189dcc`, manifest digest `unjuno-6590-geometry-preflight@sha256:d4be3c65847d7276752000268bf97c5ea9cb6ce85f93b1ffc9aced409c189dcc`, built from `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Platform `linux/arm64`; network `none`; configured 1 CPU, 256 MiB memory and 32 PIDs; root filesystem and source mount read-only; all capabilities dropped; no-new-privileges enabled. No GUI, authority or application effects.
- Candidate container `d4b99c4650b70a1807a01382e5425cac86a57fff5219e141e214e19c5d1065bf`, 2026-10-02 08:20:47.804–08:20:47.994 UTC, exit 0. Auditor container `d3413db460e858462965deafc4dce2257afa7f3552ca114be38a637ed1b49107`, 08:20:48.139–08:20:48.290 UTC, exit 0. Both were removed after inspect/log capture; their IDs and HostConfig are retained in the run record.
- Docker inspect reports configured `Memory=268435456` and `MemorySwap=536870912`. This records configuration only; actual host cgroup/swap enforcement and peak usage were not measured and are not inferred.

## Raw evidence

- Container raw JSON: `results/replication-02/candidate/raw.json`, 139,173 bytes, SHA-256 `4092bc96be090a5a441abac0adc07db44a5855247e06c68785caedf57bf2e38f`. It exactly matches the pre-freeze host construction output at `preformal/host_candidate.json`.
- Independent audit: `results/replication-02/audit/AUDIT.json`, SHA-256 `43680c27ff963be62f4b29900c987ba3e6266d9adb1a06a8d375826bcad79d5d`; `PASS_GEOMETRY_AUDIT`, 551/551 rows reconstructed, errors `[]`, geometry gate `HOLD_GEOMETRY_NOT_IDENTIFIABLE`.
- Full commands, container IDs/configuration, UTC clocks, exits and artifact hashes: `results/replication-02/RUN_RECORD.json`, SHA-256 `6b143f99aad0fc82b6b740027b0c865f40737f8a71ae63e8f2c36674fdf41fac`.
- Allocation 02 freeze and source hashes: `recovery_02/FREEZE.json` and `recovery_02/FREEZE.sha256`. Allocation 01's STOP and freeze remain unchanged.

## Scope and next decision

This confirms only deterministic geometry enumeration across the host and pinned OrbStack image, plus independent reconstruction. It does not estimate MLP accuracy, spatial autocorrelation, GUI behavior, real visual grounding, calibration, safety, or the Issue-level random-minus-block effect. The tested geometry gate is a conservative precondition for avoiding overlapping/near-duplicate positive patches; failure means this T1 design cannot proceed as frozen. Consider a larger tile or redesigned support layout only as a newly justified, additive successor; never relabel this HOLD or alter #4752/#4814/T0 evidence.
