# Native core Go v0 — retained first result

**Result ID:** `native-core-go-v0-20260915-01`  
**Dependency base:** `0f2bda3c7d9eb863714795789dcfa2ea9fe86bd5` (portable runtime v0.1 retained head / PR #97)  
**Source/plan freeze:** `48fecb2e83e2083cf8eded092d0ab24d8c55b89d`

## Disposition

**PASS_NATIVE_CORE_CONFORMANCE / NATIVE_OS_BACKENDS_STILL_UNPROVEN**.

This is an offline systems-core conformance result. It does not execute a native Windows/macOS/Wayland backend, an office application, a model, or OS input/capture.

## Frozen-source closure

Seven executable/test source paths were checked with Git's blob algorithm immediately before execution. All seven local blobs exactly matched the corresponding GitHub source blobs under the frozen branch head.

## Executed checks

- Go toolchain: Go 1.23.2.
- Full source-frozen test suite: **12/12 PASS**, zero FAIL lines.
- Deterministic C1 stress corpus: **10,000/10,000** programs, seed `20260915`, exact encode/decode round-trip.
- Fail-closed coverage includes stale observation, stale binding, lease expiry, capability/permission denial, coordinate frame mismatch, held-input discipline, unknown opcode, and exactly-one-final `release_all`.
- C1 golden vectors include `<`, `&`, `>`, Japanese text, escaped quote/semicolon, control characters and U+2028/U+2029.
- Cross-builds from the frozen stdlib-only source: **5/5 PASS** — Linux amd64, Linux arm64, Windows amd64, macOS amd64, macOS arm64.

The Linux host test command elapsed about 0.23 s and used about 72 MB max RSS, but this is diagnostic single-container data only and is **not** a runtime performance benchmark.

## Development failures retained before freeze

`DEVELOPMENT.md` preserves three useful failure classes rather than hiding them:

1. Go's default JSON string encoding differs from the Python oracle's `ensure_ascii=False` wire bytes for HTML-sensitive characters and U+2028/U+2029.
2. One intermediate repair build failed because the Unicode helper import was missing; a later golden test still failed because encoder call sites had not actually switched to the compatible quote function.
3. A Python source-generation helper using `splitlines()` reinterpreted U+2028/U+2029 as line boundaries and corrupted generated Go source.

These failures justify byte-level wire conformance tests instead of relying on semantic JSON equivalence.

## Build outputs

The retained record stores file types, byte sizes and SHA-256 for all five generated binaries. The binaries themselves are local experimental outputs and are not promoted release artifacts.

## Claims

### PROVEN within scope

- one compiled Go semantic core candidate reproduces the frozen fail-closed contract tests;
- C1 byte-level quoting can match the Python oracle on the frozen golden vectors;
- 10,000 deterministic valid programs round-trip under the compiled implementation;
- the same stdlib-only semantic core cross-compiles for five OS/architecture targets.

### NOT PROVEN

- native Windows input/capture/focus behavior;
- native macOS input/capture/permission behavior;
- Linux Wayland behavior;
- cross-platform office-task correctness;
- provider-token savings;
- Go as the final product language;
- product latency/throughput/reliability.

## H/T/D/C/U

**H:** a compiled systems-core candidate can reproduce the language-neutral portable contract without Python object layout or OS API coupling.  
**T:** fixed source; 12 deterministic tests including 10,000-program seed-20260915 stress; five-target cross-build; no network/model/GUI/input.  
**D:** PASS because all seven source blobs matched, all 12 tests passed, stress had no mismatch, and all five builds succeeded. Native OS support remains UNPROVEN.  
**C:** later native APIs may expose missing focus/scaling/permission/error semantics and require a new contract version; Go may not remain the final language.  
**U:** only Linux-host execution; Windows/macOS are cross-build-only; no Wayland/native backend; no real application or provider-token allocation.

## Successor

Do **not** duplicate three OS backends yet. The next implementation experiment should bind one real backend (Linux/X11 is the lowest-uncertainty reference) to this semantic core, run the same conformance vectors plus actual capture/input/release receipts, and only then port the backend contract to native Windows/macOS/Wayland. In parallel, the separate same-model paired codec experiment remains necessary before any token-efficiency claim.
