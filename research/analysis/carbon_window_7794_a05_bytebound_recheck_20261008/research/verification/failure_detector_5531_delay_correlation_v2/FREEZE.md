# Frozen execution record — Issue #5531 T4 successor metric repair

Allocation: `fd5531-delay-correlation-20261001-02`
Branch: `research/5531-delay-correlation-v2-20261001`
Path: `research/verification/failure_detector_5531_delay_correlation_v2/`
Frozen main: `29861fa860ad48bc47af68f2ebf330b1f5c9d842`
Pre-registration: `PLAN.md` blob `718314e5d814976cf168ec97c1c87e6cb0a9fce0`
Construction-01 (superseded seed overlap): `471fba54c1d5404196571b481a7538c191d3cfb1`
Construction-02 (final pre-freeze): `fcf724b77116b272814572222dfecab7ea4f030d`

## Exact pre-formal source identities (Git blob SHA-1)

- Runner `experiment.py`: `a29889cb58d21b9fd973018959c030fbab999ecf`
- Tests `test_experiment.py`: `ecf936308e375165fe0349dfa8bd32296e897ccc`
- Independent auditor `audit.py`: `11c49ec33bb7bc4d13e345a58a9a5561d191b60d`
- Seed base `55370000`, disjoint from predecessor scenario seeds (which ended at `55359999`).

Final construction on host CPython 3.11.9 / win32 streamed exact GitHub readbacks in memory with `python -B`: 8/8 tests passed and auditor AST parse passed. Construction-01's 8/8 pass is retained, but its overlapping seed range was found by static inspection before freeze and was superseded. No formal runner/auditor invocation has yet occurred for this allocation. The predecessor's raw and auditor are not inputs.

## Frozen formal protocol

1. Read back and verify the exact blobs above and this FREEZE blob from the branch.
2. Invoke exact `experiment.py` once via host CPython 3.11.9, `python -B`, in-memory GitHub source; set `FREEZE_BLOB_SHA` to this file's blob SHA. Preserve stdout exactly as `RAW-01.json`.
3. If runner exit is 0, invoke exact `audit.py` exactly once with the base64 raw stdout and expected freeze blob SHA. Preserve stdout exactly as `AUDIT-01.json`.
4. Any mismatch/failure remains STOP; no runner retry, audit retry, tuning, or source replacement under this allocation.

## Resource / claim boundary

Local CPU-only simulation. The issue #5085 container lease remains restricted to a different owner/allocation; do not invoke Docker/OrbStack. No LM Studio/model, GPU computation, experiment network, GUI, OS input, or effectful action. GPU is idle; model server remains stopped. Results are conditional on the synthetic distributions in `PLAN.md`, never a real detector guarantee.
