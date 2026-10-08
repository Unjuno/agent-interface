# Native GUI temporal receipt block — successor #2366

## H/T/D/C/U

- H: source-bound native-pixel evidence plus generation-bound receipts can support bounded temporal/occlusion transfer when stale, missing, or uncertain evidence yields or forwards safely.
- T: 12 sessions × 6 cases (72 rows): current relevant, current irrelevant, stale after generation shift, fresh post-shift, critical outside relevance, and missing receipt.
- D: each case uses an explicit receipt generation and active generation; stale generation is forced to `FORWARD_FULL_CURRENT` before relevance suppression.
- C: this is a control-block result only. It claims no DOOM/gameplay, arbitrary GUI, token, latency, or runtime result.
- U: all rows must pass; suppression is allowed only for current-generation irrelevant evidence; stale/missing evidence must never be suppressed.

## Result

The first implementation exposed 12 mismatches because stale generation was treated as merely irrelevant. After adding the active-generation comparison, the formal block passed **72/72 rows**.

| metric | result |
|---|---:|
| rows | 72 |
| passes | 72 |
| mismatches | 0 |
| current-generation suppressions | 24 |
| stale full-current fallbacks | 12 |
| missing full-current fallbacks | 12 |

Interpretation: the block demonstrates the intended fail-safe ordering in this synthetic control fixture. It does not establish transfer to X11, Windows GUI families, or game interaction.
