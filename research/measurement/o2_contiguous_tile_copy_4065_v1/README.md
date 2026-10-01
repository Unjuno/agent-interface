# O2 contiguous tile materialization — retained successor evidence (#4092)

This additive directory publishes the already completed conversation-local allocation `o2-contiguous-tile-copy-20260922-01` as a retrospective successor to #4065. It is **not** GitHub preregistration and it does not rerun or rewrite #4065, #2378, or the earlier vectorization HOLD.

Scientific result: `PASS_CONTIGUOUS_TILE_COPY_SCOPED` on the frozen 15-condition development-known corpus. The only mechanism change versus the immediate vector comparator is `tile.tobytes()` → `np.ascontiguousarray(tile).tobytes()` (plus class name). All AIT1 packet bytes and independently reconstructed pixels are identical. Dense candidate/vector paired median ratios are 0.4670, 0.4803974972, and 0.5084204259. The nine other changed conditions all satisfy the preregistered <=1.10 regression gate.

This is encoding-cost evidence only. It establishes no bandwidth/token reduction, model/task benefit, end-to-end desktop speedup, peak-memory bound, cross-platform result, or production readiness. No runtime/default source is modified.

Directly reviewable exact executed files include PLAN.md, FREEZE.json, ENVIRONMENT.json, AUDIT.json, CANDIDATE.diff, candidate.py, contiguous.py, schedule.json, and test_construction.py.

The four `allocation.patch.part*` files concatenate to a byte-exact git binary patch containing **all 131 original allocation files**, including every retained input pair, all three formal batches, process exits, raw timings, construction records, upstream source copies, and audit controls.

Read-only reconstruction:

```sh
python -B restore_patch.py /tmp/o2-4092.patch
rm -rf /tmp/o2-4092-review
mkdir /tmp/o2-4092-review
cd /tmp/o2-4092-review
git init -q
git apply --binary /tmp/o2-4092.patch
cd research/measurement/o2_encoding_phase_attribution_v1/contiguous_tile_copy_v1
python -B audit.py --root . --controls
```

Expected audit SHA-256: `efe9beed96288ebd32f5e4cc0d5ff0e59a322fe07d48903757edf155c9686ec5`.

Do **not** rerun the consumed formal batches. A separate held-out/current-path transfer is required before any runtime adoption.
