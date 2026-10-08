# #1564 observation gating tiny-change aHash stress

H: one global 64-bit average hash can remain unchanged under sparse must-forward GUI-like changes; hash equality must not become suppression authority. Exact fallback should restore zero false suppression but will be invoked on unchanged frames and hash-collision changes.

T: standard-library synthetic 64x64 grayscale semantics represented by 64 uniform 8x8 blocks plus sparse pixel overrides. Formal seed 155920260918001, 150,000 pairs across UNCHANGED, SINGLE_PIXEL, STATUS_DOT_2X2, CURSOR_1X3, GLYPH_STROKE_1X4, LOCAL_BLOCK_4X4 and HASH_FLIP. One invocation, reruns/replacements/tuning0.

D: every tiny family must expose >0 aHash collision/false suppression; exact fallback false suppression0 and exact unchanged suppression30000; HASH_FLIP detection>0; malformed controls fail closed; audit/corruption/source integrity pass.

C: this rejects only the frozen global aHash-style gate on this adversarial corpus, not local/task-aware/perceptual representations generally. Collision frequency is not a natural-GUI estimate.

U: no model, token, task, real-GUI frequency, latency or production claim.
