# Result — source raw hash is not reconstructible from RGB PNG

## Disposition

**PASS_RAW_HASH_NONRECONSTRUCTIBLE_FROM_PNG_SCOPED** for Issue #4106.

One formal execution of the exact frozen six-row matrix completed with exit 0; no scientific rerun, replacement or threshold/source tuning. The frozen v1 raw-only auditor also passed the observed data, but a post-formal corruption challenge found that v1 did not validate the recorded `byte_order` claim. That auditor limitation is preserved. A separately versioned **read-only audit_v2** added the missing claim checks, passed the unchanged formal bytes (88 checks, errors=[]), and rejected 10/10 copied-evidence mutations including byte_order. No encoder/formal case was rerun.

## H/T/D/C/U

**H:** 32-bit BGRX/XRGB -> RGB PNG discards the X byte, so distinct accepted raw buffers can map to the same PNG/RGB while retaining different source raw SHA-256 values.

**T:** exact current `CaptureArtifacts.write` Git blob `d20d67bc06d92d99859681f62fbeb9c2f13aab70`; width=height=1. For BGRX and XRGB: BASE, X_CHANGED, VISIBLE_CHANGED = 6 rows. Separate stdlib PNG decoder. No X server/model/input/network.

**D:** PASS iff X-only pairs have different raw SHA256 but identical PNG bytes/SHA/RGB, visible controls change PNG/RGB, and every returned source_raw_sha256 equals the submitted raw hash. All conditions passed. Versioned read-only audit_v2 and all 10 semantic corruption controls pass.

**C:** exact representation property under the accepted encoder contract. It does not claim live X servers vary X bytes, or that producer-retained source hashes are invalid.

**U:** no authenticity/currentness, live capture distribution, model/task/latency/token/product claim. Same-author separate auditor is not independent human review.

## Exact rows

| case | raw SHA-256 prefix | PNG SHA-256 prefix | decoded RGB |
|---|---|---|---|
| BGRX_BASE | c33c6e9c3e87 | 573237f67820 | 332211 |
| BGRX_X_CHANGED | 9aad152ce3ae | 573237f67820 | 332211 |
| BGRX_VISIBLE_CHANGED | fb79c2b8d894 | b6373978c6ba | 442211 |
| XRGB_BASE | d446b18e5ea0 | 573237f67820 | 332211 |
| XRGB_X_CHANGED | 0398d0ed4832 | 573237f67820 | 332211 |
| XRGB_VISIBLE_CHANGED | e4dfacffa29e | b6373978c6ba | 442211 |

Thus for each supported byte order, changing only X changes the four-byte raw buffer and its SHA-256 but leaves the exact encoded PNG bytes, PNG SHA-256 and decoded RGB unchanged. Changing visible R changes decoded RGB and PNG.

Formal RAW.json SHA-256: `11eb34ab372d33503c6e2b6403fad8b78b6d8316e99cbd0c934735a5c0bdd386`.
Read-only audit_v2 SHA-256: `7a1e0b32de2018c53abeac9bb295fbb1923676a934a89328e752070a03e7beac`.
Controls_v2 SHA-256: `0a3739de05334412f6bdcff22e4a0236392240d77a9789e4df5818e1c8076c5d`.

## Analytical proof

For one accepted pixel, BGRX maps bytes `(B,G,R,X)` to RGB `(R,G,B)`, while XRGB maps `(X,R,G,B)` to `(R,G,B)`. Let two accepted raw buffers differ only in X. Their decoded RGB arrays are equal, and the deterministic Pillow PNG encoder receives equal RGB images, so the encoded PNG bytes are equal. Their raw byte strings differ, so SHA-256 is evaluated on different messages; the observed pairs additionally verify distinct SHA-256 values. Therefore PNG+declared dimensions cannot in general reconstruct the exact original four-byte-per-pixel raw buffer or its producer-retained hash.

This is a non-injectivity statement, not a collision claim: information is discarded before PNG encoding.

## Publication/audit incidents

The initial frozen audit v1 omitted byte_order claim checking. It is retained rather than silently edited; audit_v2 is a post-formal read-only correction under the same Issue. Separately, the first RESULT.md drafting command used an unquoted shell heredoc and mangled markdown backticks. This occurred after formal execution and audits; no scientific bytes/gates changed.

## Integration consequence

Keep `artifact.sha256` (consumer-verifiable encoded bytes) distinct from `source_raw_sha256` (producer-retained lineage assertion). A PNG-only consumer cannot in general independently recompute the latter under the current 32-bit-to-RGB conversion. This result does not require storing raw captures unless a later consumer contract specifically requires independent raw-hash verification.
