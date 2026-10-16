# A saved UNKNOWN HUD is compatible with a different WAD palette

**PASS_PALETTE_COMPATIBILITY_SCOPED.** The two actual saved PNGs join their original observation RGB hashes. With only the glyph-template colors changed, the unchanged V3 scoring/geometry/threshold logic reads frame35 as health100/ammo47 using palette9. Every other palette abstains on both fields. The earlier frame31 remains health97/ammo47, accepted only by palette0. This narrows the unresolved palette/render diagnosis from #7577; it does not repair the production reader or change the original abort result.

| Saved sequence | Production palette0 health/ammo | Unique matching palette | Diagnostic health/ammo | Accepted digit score range |
|---|---|---|---|---|
| 31 | 97 / 47 | 0 | 97 / 47 | 0.9274–0.9386 |
| 35 | UNKNOWN / UNKNOWN | 9 | 100 / 47 | 0.9368–0.9591 |

All 56 field/palette outcomes (2 frames × 2 fields × 14 palettes) are retained in `run-01/result.json`. The existing 0.80 score and 0.05 runner-up margin were unchanged; palette-zero reconstruction is exactly equal to the unchanged reader. Frame35 palette-zero scores remain all zero. There was no geometry correction, threshold fitting, generic OCR, pixel recoloring, or candidate rerun. The probe records **diagnostic interpretations**, never input authority.

Execution: one saved-data invocation, exit0, 2026-10-05 04:11:51–04:11:52 UTC; CPython3.12.14, Pillow12.3.0, NumPy2.3.5, macOS27.0.1 arm64. No game/model/X11/container/GPU was used. No latency advantage or effective resource cap is claimed. `FREEZE.json` was written before invocation and binds the script, protocol, current reader closure, original events, PNGs and prior result. The external WAD matches SHA256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`; it remains in its original local custody and is not duplicated in this package.

The primary [id Software status-bar source](https://github.com/id-Software/DOOM/blob/master/linuxdoom-1.10/st_stuff.c#L954-L1002) provides the motivating mechanism: color-effect palettes differ from the base palette. This is background evidence, not proof of which branch the retained ViZDoom build took. Matching palette9 supports a compatible rendering explanation; it does not independently establish an item pickup, engine state, or correct general health recognition. Post-result visual inspection also shows apparent100/47 in frame35, but is not a blinded label or an independent dataset.

**Decision:** pursue a separately versioned palette-aware reader only after a meaningful negative/ambiguity and heldout-frame gate. The current UNKNOWN behavior must remain fail-closed until that evidence exists. Naively taking the best of14 templates enlarges the false-acceptance surface, and leading unreadable digits may be mistaken for blank slots by the existing foreground-only matcher. This study does not establish threat detection, useful early stop/switch, physical input release, bounded recovery, live throughput, or MAP01 success. #59 and the full goal remain open.

Independent raw/source audit: `audit_saved.py` uses a separate WAD/patch decoder and score reconstruction, without importing the candidate or production reader. `audit-result.json` passes144/144 checks, reconstructs every field/palette outcome and score projection, verifies the original PNG-to-observation RGB joins, candidate freeze digest and original saved-probe baseline equality. It shares Pillow/NumPy and the specified matching algorithm, so it is implementation cross-checking, not an independent labeling oracle. No candidate or live experiment was rerun. This is technical review, not a main-merge quorum vote.

Evidence is additive under this new path. #7577's first results, freezes, raw files and UNKNOWN labels are untouched. Existing #7950/#7953/#7966 concern synthetic identity/outcome boundaries; they do not supply this saved-pixel result.
