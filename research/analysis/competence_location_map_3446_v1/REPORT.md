# Competence-location map — formal synthetic construction result

Allocation: `competence-location-map-3446-20261001-01`  
Issue: [#3446](https://github.com/Unjuno/agent-interface/issues/3446)  
Frozen source commit: `c5a905f8743375a6e2a0f89bc0c435494335280a`  
Frozen main: `07c5a1bbff1ba82e0ffdcd0f521fe2102a59ad51`

## Result

`PASS_COMPETENCE_LOCATION_MAP_CONSTRUCTION_SCOPED`. The single formal candidate
run emitted 56 deterministic synthetic cases × 3 policies = 168 rows. The
separate raw-only auditor exited 0, reported no errors, and rejected all four
mutation controls. All predeclared gates passed.

| Policy | Exact known locations | Known-case YIELD | Wrong known admissions | Novel false routes | Required YIELD recall | Lookup work units |
|---|---:|---:|---:|---:|---:|---:|
| Static scope | 16/48 | 0 | 32 | 0 | 8/8 | 72 |
| Recent success only | 16/48 | 32 | 0 | 0 | 8/8 | 160 |
| Validated competence map | 48/48 | 0 | 0 | 0 | 8/8 | 1,064 |

The map exceeded each control by 32 exact known locations (gate: ≥10), routed
all 48 known cases correctly, and YIELDED on all 8 required novel cases. All
policies granted zero authority and emitted zero inputs. The static policy's
32 incorrect known-case admissions are advisory routing errors, not actions.
The map used 992 more deterministic lookup work units than static scope and
904 more than recent-success-only; these counts are a cost proxy, not measured
latency. Thus this supports the scoped synthetic discrimination claim, not a
real-world speed or product-benefit claim.

## Execution and evidence

- Docker Desktop Engine 29.8.0, context `desktop-linux`; pinned
  `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
  (`linux/amd64`).
- Construction suite: 6/6 passed in the pinned image.
- Candidate and independent auditor: separate containers, network disabled,
  read-only root, 1 CPU, 256 MiB, 32 PIDs, 16 MiB `/tmp`; source read-only.
- Candidate invocation: exactly one; no retry and no post-result tuning.
- Full raw candidate JSON is retained byte-for-byte as
  `FORMAL_RAW.json.gz` (gzip transport only; SHA-256 of the uncompressed JSON
  is in `SHA256SUMS`), beside the audit JSON, execution receipt, and checksums
  under `results/3446-competence-location-map-20261001-01/`.
- RTX 3080 Laptop GPU was idle (0%, 0 MiB). This is a deterministic CPU-only
  routing discriminator with no learned model or training, so GPU use would
  not accelerate or validate the hypothesis.

## H / T / D / C / U and interpretation

The tested H/T/D/C/U and all thresholds are preserved in `PREREGISTRATION.md`
and `FREEZE.json`; the unverified refinement is the competence-location map
idea attached to #3446, not the earlier static router result. The data are
synthetic and authored, all on one host; repeated records do not estimate a
population. No live browser/file/GUI adapter, independently measured
application effect, learned router, cross-app generalization, end-to-end
benefit, production safety, or human-team memory transfer is established.
The substantial lookup-work increase remains an open tradeoff for a real
latency/benefit experiment.

The C-drive-full interruption before this run was a STOP before candidate
execution, not a candidate failure. Docker remained running; no Docker cache,
container, or user data was removed. After storage became available, this same
frozen allocation resumed once and produced the result above.

