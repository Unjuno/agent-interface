# O2 contiguous canonical adoption — Issue #4139

## Base and scope

Base main: `e011d13decdc746dc55b0cd8a372e638a15f6ecd`.

The only shared-source change authorized by this integration decision is in
`research/observation_tiles/tile_transport.py`: changed-tile serialization
`tile.tobytes()` -> `np.ascontiguousarray(tile).tobytes()`.

No performance allocation is rerun. Performance evidence remains #4092 and
#4103/PR #4110.

## H

For the current uint8 tile representation, making a slice C-contiguous before
serializing preserves its C-order element sequence and therefore its payload
bytes. The canonical AIT1 packet, routing decision, Decoder reconstruction and
encoder state/rollback contracts should remain unchanged.

## T

1. Freeze base/source/test Git blobs before the shared-source edit.
2. Apply the one-line canonical change.
3. Run the unchanged canonical transport tests.
4. Run the existing transport-integration-v2 regression.
5. Run an additive old-vs-new byte-equivalence audit over RGB/RGBA/L,
   edge dimensions, sparse/dense/full/unchanged/resize cases and the eight
   retained #4103 golden-v3 adjacent frame pairs.
6. Preserve any incompatibility; do not tune around it.

## D

PASS_O2_CONTIGUOUS_CANONICAL_ADOPTION_SCOPED requires exact old/new wire bytes,
exact decoded target pixels, all existing regressions passing, atomic state
semantics preserved, and a diff limited to the one-line implementation change
plus additive evidence/tests.

Any wire/pixel/state mismatch rejects adoption. Missing test/source evidence is
HOLD/STOP.

## C

Prior speed evidence is retained-frame technical-repetition evidence. This
adoption gate measures compatibility, not live capture or task latency.
Temporary contiguous tiles may allocate/copy; peak RSS remains unmeasured.

## U

No token/bandwidth/model/task/human-tempo/cross-platform/product claim.
