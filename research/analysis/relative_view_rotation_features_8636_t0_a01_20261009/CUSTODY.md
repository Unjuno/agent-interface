# A01 custody note

This package preserves 13 exact source blobs from PR #8711 head `48135041a13c0988cf2d254dc5680f611063d10e`. The original candidate and auditor were not rerun. The first result remains HOLD_UNCERTAIN; no method or hypothesis pass is established.

Three original files are deliberately excluded from this main-tree copy. The first two contain user-specific local paths. The archive has macOS AppleDouble metadata and has not received comprehensive sensitive-data review. Their SHA-256 values below identify the unmodified original blobs, which remain in the public PR history and in a local private-evidence copy. That local copy is not an independent backup.

- `FREEZE.json`: `8ba8266c13792b656b864abe9a62aef3f698bf7e890586f2128433d9dc1f8093`
- `results/auditor.stdout.txt`: `34e3c43586302371732ee1acffbbaf6e8e7a0f6d672b83700041e58b85cb3a8f`
- `results/first-outcome.tar.gz`: `e85c70e879f16e57bade77f6a52b05cd75c85385ab40e3d3394b76a96753096d`

The source freeze records eight source hashes, all verified against original Git blobs. The original archive matches the hash in FORMAL_RUN.md, contains 4,766 regular tar members including AppleDouble metadata, and no independent per-file manifest was established. A narrow home-path scan found no matches inside the archive; this is not a comprehensive privacy review. The reported 2,202 output files are not a count of all tar members.
