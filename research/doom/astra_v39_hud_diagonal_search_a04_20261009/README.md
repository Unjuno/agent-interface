# V39 HUD diagonal anchor-search diagnostic A04

This model-free CPU experiment tests the explicit gap left by A03: diagonal HUD registration shifts. It keeps the A03 reader and its eight axial fallback offsets unchanged, then applies eight diagonal translations to the same 13 retained health-HUD frames.

## H/T/D/C/U

- **H:** The A03 exact-center-first reader with eight axial offsets will recover some or all diagonal shifts up to two pixels, while never emitting a wrong observed health value.
- **T:** From the exact current-main freeze `677e95fce6e5d7357d3c4c16588cdedfa31bfd69`, run one frozen candidate against 13 retained frames, eight diagonal transforms `(±1,±1)` and `(±2,±2)`, brightness/contrast/JPEG perturbations, and 13 blank-ROI controls. Use the exact A03 reader modules and fixed Freedoom WAD. Independently reconstruct every row from raw frames and test five copied-result mutations.
- **D:** PASS only for 13/13 baseline labels, 104/104 diagonal labels, zero wrong observed labels across all 182 perturbations, and 13/13 blank controls unknown. Any other candidate result remains FAIL.
- **C:** Pixel transforms are synthetic; one 13-frame historical corpus may not represent all fonts, render scales, or actual window/capture registration faults. Center-first exact reads can obscure shifts if they still classify.
- **U:** No live capture, GUI/game, binding fault, model call, OS input, input release, environment response, task effect, survival, or MAP01 outcome was measured.

## Result

`FAIL_BOUNDED_DIAGONAL_SEARCH` on execution `v39-hud-anchor-diagonal-search-a04c-20261009`: baseline 13/13; diagonal translations 2/104 correct; perturbed observed wrong 0; blank controls 13/13 unknown. The only recovered translations were `(+1,+1)` and `(-1,+1)`, each on one frame with health 11; the selected scan offset was `(±1,0)`. The other 102 diagonal cases returned unknown. Brightness, contrast, and JPEG variants remained unknown as in A03.

The measured end-to-end candidate p95 was 14.6452 ms versus 1.8911 ms for the exact-reader path (7.744×) in this one run on Python 3.13.14, Pillow 12.2.0, NumPy 2.3.4, Windows. This ratio is a single-run observation and is not a cross-version comparison with A03.

The independent auditor returned `PASS_AUDIT`, reconstructed all 195 candidate rows and 13 blank controls, and passed 5/5 mutation controls. Its inherited schema string still says `...a03-audit-v1`; the freeze, raw candidate, status, and audit command identify A04c. No candidate rerun followed the audit.

## Reproduction

Use the exact A04c main commit, the declared Python/dependency versions, and a Freedoom 0.13.0 WAD whose SHA-256 is `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`:

```powershell
py -3.13 .\analyze_a04.py --wad <path-to-freedoom2.wad> --git-root <agent-interface-checkout>
py -3.13 .\audit_a04.py --wad <path-to-freedoom2.wad> --git-root <agent-interface-checkout>
```

The official Freedoom 0.13.0 ZIP is linked from the [Freedoom download page](https://freedoom.github.io/download.html); the release checksum file reports ZIP SHA-256 `3f9b264f3e3ce503b4fb7f6bdcb1f419d93c7b546f4df3e874dd878db9688f59` ([release](https://github.com/freedoom/freedoom/releases/tag/v0.13.0)). The WAD itself is not included.

`FREEZE_A04.json`, the complete 195-row result, predecessor A02 evidence, audit output, run record, and `SHA256SUMS.txt` preserve source/data identity. The independent audit does not invoke the candidate or alter its result.
