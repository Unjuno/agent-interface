# Native core v0 — frozen offline plan

## H

A compiled systems-core candidate can reproduce the portable runtime v0.1 semantic admission and C1 wire contract without using Python object layout or any OS-specific runtime API.

## T

After source freeze, execute one retained offline allocation `native-core-go-v0-20260915-01`:

1. run the complete deterministic Go test suite;
2. run a seed-20260915 deterministic 10,000-program valid C1 round-trip corpus;
3. include stale observation/binding, lease expiry, capability/permission, coordinate-frame, held-input, unknown-opcode and terminal-release refusal tests;
4. include byte-exact golden C1 vectors with `<`, `&`, `>`, Japanese text, semicolons, escapes and U+2028/U+2029;
5. build the exact frozen stdlib-only core for Linux amd64/arm64, Windows amd64, macOS amd64/arm64;
6. retain build file types, SHA-256 hashes, toolchain/environment, test output and all exit codes.

No network, model, GUI, OS input/capture, provider tokenizer, workflow or existing formal allocation is used.

## D

PASS only if all frozen tests pass, 10,000/10,000 valid programs round-trip exactly, malformed/stale/unsafe cases fail closed, all five target builds succeed from the frozen source, and published source blobs read back equal the frozen local source.

Cross-build success never upgrades an OS backend support claim.

## C

Language-specific JSON/Unicode escaping, zero values, integer bounds, pointer/button state or error ordering may differ from the Python oracle. The native backend APIs may later expose missing semantics and require a new contract version.

## U

No native Windows/macOS execution, no Wayland backend, no real office task, no model/provider-token measurement. Single Linux host build timing is diagnostic only.

## Stop

Retain the first post-freeze allocation exactly. Do not rerun its result ID for a better outcome. A repair requires a new plan/result ID and must retain the failed first result.
