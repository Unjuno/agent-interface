# Post-run evidence correction — Issue #4983

This addendum addresses the two evidence-integrity findings on PR #4991 using retained artifacts only. It does not alter or replace the frozen allocation, its runner, `RAW.json`, the original `AUDIT.json`, or its `STOP_NO_CONSTRUCTION_COMPETENCE` disposition.

## Initialization provenance

The retained `INITIAL_WEIGHTS.npz.b64` decodes to SHA-256 `d62bdd9216c0b969b7872b1da7c11a517a376b04ff351b46d6629a5ef2cb32f9`. Reconstructing the NumPy initialization at seed `58100472` matches all eight saved tensors exactly across the max-only and max+mean arms. This confirms that the declared seed was applied to the saved initial weights.

Reproduce with:

```powershell
python research/analysis/tiny_visual_extent_init_sensitivity_4817_v1/postrun_audit.py
```

The script checks the raw and decoded-weight digests, allocation/seed identity, all eight seed-derived tensors, and the held-array ordering read from the frozen runner source. The machine-readable receipt is `POSTRUN_AUDIT.json`.

## Held-center labels

The frozen runner stores arrays by lexicographically sorting stringified tuple keys, but writes `held_centers` using numeric tuple sorting. Five positions (0, 2, 4, 6, 7) therefore have misleading center labels. The actual held-array order is:

`(14,22), (14,8), (20,25), (20,8), (26,22), (26,8), (32,15), (8,15)`.

The recorded metadata order remains preserved in the original raw file. Use the actual order above to interpret each `held_i` array. All eight held-positive ACCEPT values are 1.00, so correcting these labels leaves the aggregate unchanged.

## Disposition

`PASS_SEED_BINDING_WITH_CENTER_LABEL_CORRECTION` is limited to the post-run provenance check. The scientific disposition remains `STOP_NO_CONSTRUCTION_COMPETENCE`: max+mean train/base accuracy is 0.50/0.50. No fit, CUDA invocation, threshold change, or formal row was added.
