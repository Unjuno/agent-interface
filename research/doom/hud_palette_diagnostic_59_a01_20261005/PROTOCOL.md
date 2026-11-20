# A01 saved HUD palette diagnosis

This is new, finite analysis of retained evidence from #7577, not a replay of either live construction or the original saved probe. No runtime change, GUI, model, container, game, or positive input. Source: main `86748499a89141396902a00d1f5793390ccf6d9d`. Parent #59; worker 01a0ff52. One host CPU process, two retained PNGs, finite WAD palettes, output below 1 MiB expected. No performance claim; no asserted OS-enforced CPU/memory cap.

H: replacing the fixed first PLAYPAL palette with another palette from the same hash-bound WAD is sufficient to restore the exact glyph match for the retained UNKNOWN observation. This is a compatibility diagnosis, not independent health ground truth or evidence that the engine selected a particular palette.

T: use exactly saved sequences 31 and 35 (selected because the existing report identifies them, not a heldout sample). Verify PNG RGB against the original observation's frame hash. Run unchanged current V3 `read_frame` for health and ammo at each retained geometry. Then replace only its glyph-template RGB using every complete WAD PLAYPAL palette. Keep masks, nearest resize, geometry, 0.80 score, 0.05 margin and right alignment unchanged. Save every outcome/score. Palette zero must equal the original reader. Stop on any input/hash/parser mismatch. One diagnostic invocation; no threshold search or retries to obtain success.

D: `PASS_PALETTE_COMPATIBILITY_SCOPED` requires sequence31 original values97/47 unchanged and sequence35 both fields observed under one unique shared nonzero palette, with no conflicting accepted values at other palettes. If no such palette exists, `FAIL_PALETTE_ONLY_EXPLANATION` for this exact finite palette substitution. Multiple incompatible accepted values produce `UNCERTAIN_PALETTE_AMBIGUITY`. None grants controller authority. All first results retained.

C: renderer may use blended/gamma-adjusted colors absent from PLAYPAL; geometry, scaling, occlusion or an actual glyph change can contribute. Testing a finite palette bank increases the multiple-match surface; the existing foreground-only matcher does not validate blank leading slots. No broad accuracy or repair acceptance follows even from a positive case.

U: two correlated failure-selected frames, one WAD, one observed geometry; no independent human/scorer labels, negative-image suite, heldout episode, live timing, release or useful-control result. Original UNKNOWN and live abort remain valid. An independent raw/source audit will check reconstruction without running the diagnostic again.

Primary background: [id Software status-bar source](https://github.com/id-Software/DOOM/blob/master/linuxdoom-1.10/st_stuff.c) selects alternate palettes for visual effects. This motivates the hypothesis only; the retained ViZDoom renderer is not assumed to implement that exact path. No external source code is copied into this package.
