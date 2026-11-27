# V15 current-main release producer to attribution adapter, T6

## H / T / D / C / U

**H.** The exact current-main V15 release-batch producer methods emit a multi-batch delivery ledger that the T5 fail-closed adapter can consume without promoting incomplete rows to a unique temporal attribution.

**T.** Freeze current main `e627b8954ecfbdd90ccfe35a81441a00d88047c8` and the T5 adapter source at PR #8513 head `cebc4239cab5bd4d83b0cf8a32e945d536b9d7f0`. AST-execute the exact backend `_delivery_ledger`, `_set_delivery_state`, and `_publish_release_batch` methods for two single-key releases in one program stream. Supply inert owner receipts and independent scorer samples, pass the emitted rows directly to T5, then inject mixed schema, duplicate/gapped positions, a missing final release row, and input-row reordering.

**D.** The unmodified producer output must have delivery positions 0 and 1, confirmed ledger states, and a verified non-authoritative release receipt; T5 must return `SOURCE_ROWS_JOINED / TEMPORALLY_UNIQUE` with causal attribution still `NOT_ESTABLISHED`. Mixed, duplicate, and gapped positions must be `HOLD_INCOMPLETE_RELEASE_BATCH / UNRESOLVED`. A missing release row must not retain a unique label. Reordering input rows must preserve the baseline disposition.

**C.** This verifies producer-method/adapter data-contract composition for one deterministic two-release stream. Owner state and scorer feedback are synthetic.

**U.** No full runtime, owner thread, physical OS state, GUI, game, model, live threat, actual task progress, or causal effect is exercised. `TEMPORALLY_UNIQUE` is only a verified-bound temporal association and does not establish causality or application consumption.

## Result

See `RESULT.json`, raw normal/optimized outputs, and `verify.py`. The candidate adapter is bundled byte-for-byte from T5 so this package does not depend on a mutable remote branch.

## Reproduction

From repository root, run:

```powershell
python -B research/doom/v15_release_batch_t6_20261008/run_modes.py
python -B research/doom/v15_release_batch_t6_20261008/verify.py
```
