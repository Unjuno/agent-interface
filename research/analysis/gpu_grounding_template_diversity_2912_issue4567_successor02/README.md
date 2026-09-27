# Held-out form-template GPU experiment — corrective successor

Issue #4567 is the canonical record for this distinct allocation. It follows the immutable STOP in #4546; no outcome or model result transfers from that attempt.

- The synthetic raster corpus and manifest are carried forward unchanged from the #4546 construction commit. This is not a new independent data collection.
- `train_eval.py` resolves every manifest image beneath `corpus/`, verifies each image SHA-256, and rejects path traversal before training.
- `test_construction.py` adds an explicit 240-image resolver/hash regression test.
- The only formal run remains gated on fresh local GPU-idle serialization evidence, complete source readback and a one-shot acknowledgement.

This is a synthetic-only visual-regression experiment, not evidence of performance on real applications. No predicted point is sent to a GUI or granted action authority.
