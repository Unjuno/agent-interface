# Source snapshots

These two `.txt` files are byte-for-byte archival copies from the final PR #7395
head `ece144c6c9304ffda03cb3d32beff06acdc986da`:

- `source/doom_typed_release_backend_v3.py.txt`
- `source/test_doom_typed_release_backend_v3.py.txt`

`SOURCE_SNAPSHOT_SHA256SUMS` verifies these copies. They are kept separate from
the live source paths because current `main` has different versions there.
Historical run records remain bound to their own frozen source hashes; these
final-head snapshots must not be substituted for those intermediate sources.
No candidate or live allocation was rerun to create this archive.
