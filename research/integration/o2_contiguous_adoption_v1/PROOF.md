# Byte-equivalence argument

The canonical O2 encoder obtains each changed tile as a NumPy `uint8` view
`b[y:y+size, x:x+size]` and serializes it with `ndarray.tobytes()`, whose
default order is C order.

The adopted expression `np.ascontiguousarray(tile).tobytes()` first produces
an array with the same shape, dtype and element values laid out contiguously in
C order, then serializes that same C-order element sequence.

For the canonical supported modes (L/RGB/RGBA), one array element is exactly one
payload byte. Therefore, for every tile coordinate and geometry used by the
encoder, the emitted tile payload byte sequence is unchanged. Tile headers,
tile ordering, metadata, compression level, full-frame alternative and
shorter-packet selection are not changed.

The implementation tests in this directory check the executable obligations:
old/new packet identity, decoder reconstruction, edge dimensions and modes,
unchanged/full/sparse/dense routing, rollback on materialization failure, and
the retained golden-v3 frame pairs.
