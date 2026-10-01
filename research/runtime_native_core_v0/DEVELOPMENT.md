# Development calibration retained before source freeze

These are **development findings**, not the retained post-freeze allocation.

1. The first Go implementation used `encoding/json.Marshal` for C1 text/predicate quoting. A direct comparison against Python `json.dumps(..., ensure_ascii=False)` showed byte differences for `<`, `&`, `>` and U+2028/U+2029.
2. An explicit Python-compatible UTF-8 quote function was added. The first build after that edit failed because `unicode/utf8` was not imported.
3. After the import fix, the golden wire-vector test still failed because the encoder call sites were still using `json.Marshal`; the quote function itself passed its unit vectors.
4. Replacing the encoder call sites closed the observed byte mismatch.
5. A local helper that combined Go test source using Python `splitlines()` corrupted a fixture containing U+2028/U+2029 because Python recognizes those Unicode separators as line boundaries. The generated file failed to compile. The helper output was discarded, the real source files were preserved, and golden expectations were rewritten to construct U+2028/U+2029 explicitly by code point.
6. The repaired development build passed 12 tests including a deterministic 10,000-program C1 round-trip stress corpus.
7. The repaired development source cross-built stdlib-only binaries for Linux amd64/arm64, Windows amd64, macOS amd64/arm64.

The failures above are retained because they expose a real portability hazard: semantic JSON equivalence is weaker than byte-level wire compatibility, and even source-generation tooling can silently reinterpret Unicode separators.

The formal retained allocation begins only after the GitHub source/plan freeze and source readback.
