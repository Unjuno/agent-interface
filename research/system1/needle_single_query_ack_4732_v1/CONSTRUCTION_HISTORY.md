# Construction history — Issue #4732

Allocation `needle-single-query-ack-6842791-6842793-6842797-v1`; formal seeds 6842791/6842793/6842797 have not run. Every construction output and volume is retained separately; no deletion or overwrite.

## Environment

- Docker client/server 29.8.0.
- Cached image `needle-pilot05:local`, Linux/amd64, exact image id in `FREEZE.json`; no image pull/install.
- Network disabled; read-only root and source; CPU 1, 2 GiB RAM, 64 PIDs, no-new-privileges, bounded noexec/nosuid tmpfs.
- Frozen #4714 `study.py` mounted read-only as the common synthetic data/model/snapshot implementation.

## Construction run 1 (retained; pre-freeze)

Construction seed 6842783, fresh construction-v1 local volume and output. Runner completed INLINE_512 then ONLINE_QUERY_ONLY for 12 arrivals each. Separate auditor returned `CONSTRUCTION_AUDIT_PASS`: 24/24 arm-arrivals exact for adapter/optimizer snapshots, query and full held-out vectors; actual final volume bytes matched; audit errors 0; 5/5 corruption controls rejected.

Ack p95 was 102.086/95.081 ms. Stage timing had one large update outlier (~86 ms) in INLINE_512 and a commit outlier (~92 ms) in ONLINE_QUERY_ONLY. This single construction seed is not an effect estimate. Review found the formal seed block was all odd; the original parity-based arm-order selection would not alternate formal order. That construction-only code was discarded before freeze; formal seeds were untouched.

## Construction correction and run 2

Runner now uses explicit seed-to-arm-order mapping (6842791 INLINE first; 6842793 query-only first; 6842797 INLINE first) and sets one deterministic torch CPU thread in each resident child. The auditor reports update, query, full-batch, commit, acknowledgement, and total arm elapsed times separately. Five Docker construction tests passed.

Construction seed 6842783 was used again strictly for construction in a second unique output tree and new volume `unjuno-needle-single-query-ack-4732-construction-v2`; v1 artifacts remain unchanged. Separate audit again passed 24/24 arm-arrivals, exact snapshot/prediction parity and actual final bytes, zero errors, 5/5 corruption controls rejected. Ack p95 was 15.590 ms inline vs 15.121 ms query-only (ratio .970); full-batch prediction p95 0.644/0.843 ms, one-query p95 0.225 ms, commit p95 11.675/10.255 ms. Total measured arm elapsed 482.542/481.041 ms for 12 arrivals. This is still construction evidence only, not formal inference.

Both construction runs' raw `run.json`, exact worker input, and separate `AUDIT.json` are retained under the corresponding `construction/` and `construction-v2/` directories in this evidence bundle. `CONSTRUCTION_MANIFEST.json` binds each byte length and SHA-256; both run trees remain permanently excluded from formal inputs.

## Freeze boundary

At initial construction there was no source freeze and no formal container run. The current files and hashes in `FREEZE.json` are published and read back before the exact one-shot formal commands. Formal work uses fresh directories and a distinct fresh volume; no construction output is a formal input. No retries, tuning, replacement seeds, or post-result extension.
