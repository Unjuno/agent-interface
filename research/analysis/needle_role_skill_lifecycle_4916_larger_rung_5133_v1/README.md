# Corrected lifecycle amortization experiment — Issue #5133

This is a fresh executable successor to #5084. It preserves #5084/-01,
#5084/-02, and the read-only STOP in #5125 without changing their recorded
files or allocation identities. The -02 entrypoints expected a sibling freeze
inside the v1 source directory, while its freeze was in v2; the runners also
hard-coded -01. This package co-locates its own freeze and launchers, and the
launchers bind all three frozen v1 modules to the same v3 root and new -03
allocation at runtime. The wrapper and imported source hashes are all pinned.

The pre-registered design is 15 paired alternating AB/BA blocks, 1,000
requests per arm per block (30,000 predictions), exact retained-prediction
reconciliation, and a separate raw-only audit with seven mutation controls.
See `FREEZE.json` for all conditions and commands. This remains one synthetic
seed and pure-Python lifecycle evidence only.

The freeze is based on current main `e8b4071931df81b3408a5d0a91c7607c6323c9c9`.
This bundle is preparation only. It must pass local tests, source/path/hash
preflight, and receive an explicit named Docker/OrbStack CPU-slot assignment
before any container invocation. No experiment result is implied.
