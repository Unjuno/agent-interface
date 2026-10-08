# Astra V39 HUD reader cross-run transfer A01

## H / T / D / C / U

- **H:** The current-main V39 WAD-glyph health reader can recover the manually transcribed health value from each of the 13 exact model-input frames retained for `map01-astra-attempt-v1`, when supplied that frame's original capture sequence, monotonic capture time, and X11 window binding.
- **T:** Run the frozen `DoomStatusNumberReader` once over the 13 retained PNGs. Require each PNG SHA-256 to match both retained frame manifests and its originating observation path; use the observation's original `sequence`, `capture_ns`, and `pointer_binding`. Compare values with the `HEALTH` transcription constant in the frozen post-hoc analysis. Then blank only the health-number ROI in memory and require all 13 negative controls to return `unknown`.
- **D:** `PASS_CROSS_RUN_HEALTH_READER` requires 13/13 exact source-frame joins, 13/13 `observed` values equal to the frozen manual values, all original metadata preserved, and 13/13 blank-ROI controls returning `unknown`. Any mismatch is retained as FAIL or HOLD; no thresholds are tuned after seeing results.
- **C:** The known manual labels or the source game's glyphs could differ from the current reader assumptions. The blank-ROI control tests only one obvious missing-signal case, not all image corruption or ambiguity modes.
- **U:** This is an offline cross-run reader-transfer result for 13 sparse decision frames. It does not recover the other 517 observations' pixels, reproduce the live signal monitor, show when health changed during model waits, establish guard crossing/cancellation/release timing, or prove useful feedback, recovery, survival, progress, or MAP01 completion.

## Provenance

Freeze against repository `main` `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. The 13 PNGs are exact byte matches between `frame-manifest.json` and `local-exact-frame-manifest.json`, joined to the report's `source_image` and the corresponding exact observation event. All 13 carry the same recorded X11 binding geometry `[321, 180, 640, 480]`; the image canvas is 1280×800. The health transcription oracle is read as an AST literal from the separately hash-pinned `analyze_map01_astra_failure_v1.py` without importing or executing that analysis.

The WAD is supplied as a local external input and is accepted only at the exact SHA-256 already required by the V39 HUD reader. Its path is intentionally not retained in the result. The run used the bundled macOS Python 3.12.14 runtime with Pillow 12.3.0 and NumPy 2.3.5; it read retained files only and launched no game, model, GUI, OS input, container, or shared service. `results/a01.json` records 13/13 exact matches and 13/13 blank-ROI `unknown` controls. The artifact audit passed all five copied-result mutation controls. This is an offline reader-transfer PASS only; the live computer-control exit gate remains open.

The execution freeze is based on `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. A post-run identity check found that `origin/main` at `798ac5ad709168ff1d27b115f10f4f96b126bb71` has identical Git blob IDs for all four pinned reader/oracle source files. This supports transfer to those byte-identical source files only; the allocation was not executed on the newer full repository tree.

## Reproduction

From the repository root, run once:

```sh
python3 research/doom/astra_v39_hud_reader_transfer_a01_20261007/analyze.py --wad /path/to/hash-matching/freedoom2.wad
python3 research/doom/astra_v39_hud_reader_transfer_a01_20261007/audit.py
```

The first command was run once for execution `astra-v39-hud-reader-transfer-a01-20261007`; do not rerun that frozen execution. Use a new execution ID and freeze for any successor experiment.

`FREEZE.json` records source blob IDs, file hashes, the WAD hash, runtime versions, and the candidate/auditor hashes. `results/a01.json` contains the per-frame reader output and bounded control results; `results/audit.json` contains the independent artifact and mutation-control audit.
