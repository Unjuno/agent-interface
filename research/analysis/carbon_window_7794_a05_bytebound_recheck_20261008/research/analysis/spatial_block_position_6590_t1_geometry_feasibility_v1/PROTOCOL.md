# Preregistered no-fit geometry feasibility protocol — Issue #6590

## H / T / D / C / U

- **H:** OrbStack reproduces the pre-freeze host construction enumeration byte-for-byte, and an independent raw-only auditor reconstructs every coordinate and eligibility label. This is a replication of a known construction result; the host exploratory count is 6/6/3/3.
- **T:** Enumerate all integer target centers that keep the 9×9 patch fully visible and do not touch the image boundary. Assign centers to northwest/northeast/southwest/southeast by strict split lines x=20 and y=15. An evaluation center qualifies for a block only if it is at least 9 pixels away in Chebyshev distance from every training support center, so its 9×9 target footprint is disjoint from every training target footprint. Candidate once; independent auditor once; retries zero. No model fit or old allocation replay.
- **D:** `REPLICATION_PASS_WITH_GEOMETRY_HOLD` iff the container candidate's exact raw bytes equal the retained host construction output and the auditor independently reconstructs it with no errors. The visual-model allocation remains `HOLD_GEOMETRY_NOT_IDENTIFIABLE` because fewer than 8 independent sites exist in at least one quadrant. `STOP_REPLICATION_DIVERGENCE` on a byte mismatch and `HOLD_AUDIT_INTEGRITY` on any audit mismatch. This is not a blind test of the already observed geometry count.
- **C:** This is a finite coordinate/patch-footprint calculation for the synthetic task, not an evaluation of model outputs or real GUI layouts.
- **U:** It does not estimate visual accuracy, spatial autocorrelation, human/agent performance, calibration, safety, or deployment effects. A larger canvas/support redesign is outside this allocation.

## Frozen geometry

- Tile: 40 columns × 30 rows.
- Fully visible target centers: integer x=4..35, y=4..25; the no-edge-touch preflight domain is x=5..34, y=5..24.
- Positive training-support centers: (20,15), (8,8), (32,8), (8,22), (32,22).
- Positive patch: 9×9 pixels centered at the target coordinate.
- Four strict quadrants exclude x=20 or y=15. Coordinates are the independent spatial units.
- No-overlap rule: two 9×9 axis-aligned patches do not overlap iff `max(abs(dx), abs(dy)) >= 9`. Thus near-duplicate exclusion is explicit and auditable, rather than inferred from different random noise.
- Minimum independent sites: 8 per quadrant, fixed before enumeration.

## Execution boundary

The source and image are frozen and pushed before the formal enumeration. Candidate and auditor run once each in separate, new OrbStack containers using the same digest-pinned Python 3.12 slim image, `--network=none`, one CPU, 256 MiB memory, 32 PIDs, read-only root and source mounts, and separate output mounts. No shared container is read or changed. Container stdout/stderr, IDs, timestamps, raw enumeration, independent audit and hashes are retained. There is no network access from either formal container, no model, no GPU, and no GUI or application effect.
