# Excluded construction — issue #4448

Disposition: `CONSTRUCTION_AUDIT_ACCEPT`. This is excluded protocol/construction evidence, not the 12-pair formal result; none of these rows are pooled into formal data.

## Run and independent audit

- Local Docker Engine 29.8.0; pinned cached image and environment are in `ENVIRONMENT.json`.
- Three matched pairs, four actions per arm, fixed alternating order, schedule ID `construction-20260927-r1`.
- Docker invocation: runner `--output /evidence/construction-29 --pairs 3 --schedule-id construction-20260927-r1 --label construction-excluded`; network disabled, root filesystem read-only, and `/tmp` plus `/dev/shm` tmpfs.
- The copied retained evidence in this directory was independently re-audited inside the same pinned local Docker image. Baseline `audit_errors=[]`; 12/12 effective copied-evidence corruptions were rejected.
- Raw SHA-256: `2cd5199a67fa50965ef89c2463b363fa677f2c0b03c5884ffa7f141db4436e3a` (31,858 bytes).
- Construction audit SHA-256: `64dc877b80f1843f1cd11e9ed6d6c7a04e9ca8d7246648fb4deffe2fab7fd949`.

The retained scratch evidence includes effect files, the byte snapshots and hashes seen by the observer, child-ready and normal-exit receipts, per-XTerm stderr, and the Openbox/Xvfb stderr. Across both arms, every effect line is exactly `{"value":"r"}\n`; all 24 XQueryKeymap snapshots are 32 zero bytes. Per pair, ephemeral XTerm and child PIDs are four distinct IDs; resident XTerm and child PIDs remain constant across all four actions. All XTerm, Openbox and Xvfb exit codes are 0, and child done receipts report the planned action counts.

## Excluded timing summary

Percentiles use nearest rank. Timing is effect-file observation to next-ready; ephemeral next-ready follows native XTerm exit, while resident per-action readiness follows effect receipt plus neutral keymap. The final resident XTerm exit is included in session duration.

| Arm | Actions | p50 | p95 | Median arm session |
|---|---:|---:|---:|---:|
| Ephemeral XTerm | 12 | 17.211712 ms | 18.277293 ms | 817.644 ms |
| Resident XTerm | 12 | 1.536429 ms | 2.478547 ms | 192.046 ms |

The median of the three matched-pair resident/ephemeral action-median ratios is `0.0932709`; resident session duration is lower in 3/3 pairs (ephemeral/resident ms: 666.343/179.158, 860.895/192.046, 817.644/228.431).

Construction supports a scoped latency and session-duration difference in this image, but ephemeral p50 is well below the frozen formal PASS requirement of >100 ms. If formal timing resembles construction, the required result is HOLD. No threshold or endpoint is changed, and only the one frozen formal allocation may determine the formal disposition.
