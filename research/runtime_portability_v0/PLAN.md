# Portable runtime v0 — frozen offline plan

## Scope

This task builds a **language-neutral contract oracle**, not a native OS backend and
not a new live benchmark. Existing runtime/research evidence is read-only.

## H

A small semantic program + backend-capability contract can represent Linux,
Windows and macOS without OS-specific semantics, while a compact fixed grammar
can reduce model-visible representation bytes yet decode to the identical
validated semantic AST.

## T

1. Run the source-frozen Python unit suite.
2. Run exactly one retained finite codec/conformance allocation with seed
   `20260915`, 1,000 deterministic office-like programs, and lifecycle use counts
   `1,2,4,8,16,32,64`.
3. C0 is canonical minified JSON. C1 is a fixed textual grammar. C2 is an exact
   persistent workflow dictionary guarded by epoch + SHA-derived digest.
4. Compare UTF-8 bytes and decode cost only. Do **not** call bytes "tokens".
5. Run no GUI, model, OS-input, network, package installation, or existing formal
   allocation.

## D

PASS contract only if the same representative semantic program is admissible
under synthetic fully-capable Linux/Windows/macOS profiles without changing its
AST, while unknown/unimplemented profiles remain not-ready.

PASS codec only if all 1,000 C0/C1 cases round-trip exactly and dictionary
references round-trip exactly. Unknown/malformed opcodes and stale dictionary
identity must fail closed in tests. Size reduction is secondary to correctness.

## C

Failure can occur if the purported common semantics still encode X11-only
assumptions, coordinate frames are underspecified, held-input/release cannot be
represented safely, or the compact codec merely moves ambiguity into parsing.

## U

No native OS execution is performed. No exact model tokenizer/provider usage is
available in the container, so token savings remain unknown. Decode timing is
single-host diagnostic data, not a product performance claim.

## Stop

Retain the first finite result. Do not rerun this allocation ID for a better
number. Any successor must use a new result ID and explain the changed condition.
