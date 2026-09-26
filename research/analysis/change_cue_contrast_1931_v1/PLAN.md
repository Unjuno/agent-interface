# #4436 — source-preserving contrast-guaranteed change cues

## Claim
This first rung tests only a precondition for model-facing change cueing: whether a deterministic cue can preserve every changed source pixel while making the cue location contrastive across arbitrary source colors, including edge/corner targets.

It does **not** test Astra/VLM accuracy, task success, tokens, latency, or attention tunneling.

## H/T/D/C/U
See Issue #4436. The formal allocation uses the constants frozen in `FREEZE.json`.

## Arms
- `FIXED_GREEN_OUTLINE`: 1px outside outline, RGB `(0,255,0)`.
- `ADAPTIVE_BW_OUTLINE`: 1px outside outline, black or white chosen by local background luminance to maximize WCAG-style contrast.
- `DUAL_BW_OUTLINE`: black distance-1 + white distance-2 outside strokes, clipped to the source canvas.
- `PADDED_DUAL_BW_OUTLINE`: deterministic 2px source-canvas padding, then the same dual outside strokes.

The raw current observation is retained separately in all arms. Cue pixels are never allowed inside the changed ROI.

## Formal corpus
- all 256 grayscale RGB colors `(v,v,v)`;
- RGB lattice `{0,32,64,96,128,160,192,224,255}^3`;
- de-duplicated union;
- 64x64 before/current frames;
- ROI sizes `1x1`, `2x2`, `4x4`, `8x4`;
- locations `center`, `left`, `top`, `top_left`, `bottom_right`.

Before is a uniform background. Current differs only inside the ROI, where each channel is complemented (`255-c`). The candidate derives the changed bbox from exact before/current byte differences; the authored ROI is used only by the independent scorer.

## Primary metrics
1. changed-ROI bytes preserved exactly;
2. exact source hash retained independently;
3. source/presentation inverse coordinate map exact;
4. expected-vs-actual cue geometry and clipping fraction;
5. WCAG-style local luminance contrast against the unchanged source background;
6. fixed-green low/zero-contrast witnesses;
7. adaptive/dual black-white contrast lower-bound reconstruction.

## Analytical bound
For a source relative luminance `L in [0,1]`:

- black contrast = `(L + 0.05) / 0.05`
- white contrast = `1.05 / (L + 0.05)`

Their product is exactly 21, so `max(black, white) >= sqrt(21) ≈ 4.58257569495584`.

This is a presentation-contrast bound only, not a model-attention guarantee.
