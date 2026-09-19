# Runtime native core v0

This is a **stacked systems-core conformance experiment** over the portable runtime contract retained in PR #97. It is not a promoted runtime and it does not implement native OS input/capture backends.

## Purpose

The existing Python contract oracle is optimized for research iteration. This lane asks a narrower implementation question: can the same semantic admission and C1 wire rules be reproduced by an actually compiled systems/runtime implementation without inheriting Python object layout as the ABI?

The candidate here is Go 1.23 because that toolchain is present in the isolated container. This does **not** select Go as the final product language.

## Scope

The core covers:

- backend capability manifests and permission states;
- observation/binding freshness;
- lease expiry;
- coordinate-frame admission;
- held keyboard/button state;
- exactly one final `release_all`;
- deterministic C1 encode/decode;
- byte-level Python-compatible JSON string quoting for C1 text/predicate fields.

No model SDK or OS API is linked into the core.

## Platform claims

The same stdlib-only core is cross-compiled for Linux amd64/arm64, Windows amd64, and macOS amd64/arm64. Cross-compilation is only evidence that the semantic core compiles for those targets. It is **not** evidence of native Windows/macOS/Wayland input, capture, focus, permission, or office-task support.

## Dependency

Semantic source of truth for this experiment is the fixed PR #97 retained head:

`0f2bda3c7d9eb863714795789dcfa2ea9fe86bd5`

The Python oracle remains read-only.
