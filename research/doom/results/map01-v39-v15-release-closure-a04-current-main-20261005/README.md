# MAP01 V39 V15 release closure A04

## Purpose and hypothesis

This successor to A03 checks whether the exact selected V15/V39 release-batch static Python import closure changes when `main` advances from `22e25aa74cac30f629209555ba93ba3cd2a279f3` to `c1d03aca16ba4d3ffcc6c63b907a6fc11a91be5d`.

**H.** The six selected V15/V39 startup entrypoints retain the same static import closure and blob identities across these two main commits.

**T.** Recursively parse Python AST `import` and absolute `from` statements from the six frozen entrypoints at exact `origin/main`; resolve repository modules only in the configured flat research roots; capture all source blob SHA-1 and content SHA-256 identities, unresolved configured-local imports, and external import roots.

**D.** Pass requires pinned source SHA `c1d03aca16ba4d3ffcc6c63b907a6fc11a91be5d`, exact manifest recreation, 38 sources, zero unresolved imports under configured prefixes, all source blob hashes matching, and external roots `PIL,Xlib,numpy,vizdoom`.

**C.** The A04 manifest contains the same 38 paths and identical Git blob IDs as A03 at `22e25aa74cac30f629209555ba93ba3cd2a279f3`; there are zero added, removed, or changed source blobs. This confirms closure stability for the selected entrypoints over that main advance.

**U.** This is static provenance only. It does not execute/import production code or establish dynamic/native dependency closure, owner identity, release timing, useful feedback, recovery, threat response, or task effect. It does not satisfy #59's live threat-exposure gate. No container/display/game/model/input was used; the WSLc inventory was empty but host disk was only about 1.4 GB free and this Git-object-only audit did not need a container.

## Reproduction

From the repository root with the exact source commit available as `origin/main`:

```powershell
python -B research/doom/results/map01-v39-v15-release-closure-a04-current-main-20261005/derive_current_closure.py
python -B research/doom/results/map01-v39-v15-release-closure-a04-current-main-20261005/audit_current_closure.py
```

The builder pins the run's source commit in `IMPORT_CLOSURE.json`. The separate verifier checks that the current `origin/main` still matches, re-derives the closure, and compares the entire manifest and every blob/content digest. Raw outputs and commands are in `RUN_RECORD.md`; file hashes are in `SHA256SUMS`.

Current exact result: `PASS_STATIC_IMPORT_CLOSURE`, 38 files, 0 unresolved configured-local imports, external roots `PIL,Xlib,numpy,vizdoom`. Wrong-head and modified-blob mutation controls both reject. Python 3.11.9 bytecode compilation passes for builder and verifier.

The next runtime-level owner-selection test remains a separate, explicitly frozen construction candidate. Current main does not yet contain the stacked #8065 per-key measurement route; #8094 is a draft guard on that stack, and a different worker's fake-X sample-custody repair is active. Do not treat this static closure as permission to overlap those changes or to start a private live allocation.
