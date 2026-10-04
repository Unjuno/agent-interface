# Pending-observation stream diagnostic

This is a **posthoc metadata audit** of the frozen failed `map01-astra-attempt-v1`, not a prospective allocation or preregistered experiment. It uses the exact saved `events.jsonl`, `report.json`, and `local-exact-frame-manifest.json` to quantify observation cadence during model waits and whether the exact screenshot hash changed relative to the last pre-call sample.

## H / T / D / C / U

- **Question:** Did the saved stream contain exact, hash-manifested observations during model inference, and what was the observed sampling interval and full-frame hash novelty?
- **Test:** Join all observation events by image basename to the 419-entry manifest, then join each event capture timestamp to the 13 model-call intervals. For every wait, record observation count, maximum internal capture gap, first changed full-frame SHA relative to the last pre-call image, and whether the reported fresh plan sequence equals the last observed sequence.
- **Disposition:** `PASS_METADATA_ONLY` means all observations were exact, mapped to a manifest record, and had unique sequence numbers; each model wait had samples; all reported plan sequences matched their last sampled sequence; no join mismatches occurred. This is metadata integrity only.
- **Competing explanation:** A changed full-frame SHA may reflect animation or other incidental pixels; it does not establish a health-ROI change or a material task-state transition.
- **Uncertainty:** The manifest contains hashes and byte sizes, but the intermediate PNG bytes are absent from this checkout. Therefore this audit cannot inspect pixels, rerun the health guard on intermediate samples, measure detection-to-abort latency, infer a safe action, or establish threat response. It is a single-run retrospective analysis.

## Reproduce

From repository root:

```powershell
python research/doom/map01_astra_hud_pairs_a01_20261005/stream_diagnostic.py
python research/doom/map01_astra_hud_pairs_a01_20261005/audit_stream_diagnostic.py
python -m unittest discover -s research/doom/map01_astra_hud_pairs_a01_20261005 -p test_stream_diagnostic.py -v
```

`STREAM_FREEZE.json` binds the exact base, inputs, source, and analysis code. `STREAM_RESULT.json` retains per-wait measurements. The entry is added to the package checksum manifest.
