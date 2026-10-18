# MAP01 V39 V15 release closure A05

## Purpose and hypothesis

A05 rechecks the selected V15/V39 release-batch static Python import closure at `b5be19963454ce5edafc945b78b100012952dd15`, the exact `origin/main` tip observed on 2026-10-05, following A04's check at `c1d03aca16ba4d3ffcc6c63b907a6fc11a91be5d`.

**H.** The six selected V15/V39 startup entrypoints retain the same static import closure and blob identities at the new main tip.

**T.** Recursively parse Python AST `import` and absolute `from` statements from six fixed entrypoints using only Git objects at the pinned commit; resolve modules in the configured flat research roots; record source blob SHA-1, content SHA-256, unresolved configured-local imports, and external roots. Run a separate verifier and wrong-head/modified-manifest negative controls.

**D.** Pass requires the pinned `origin/main` SHA to match, identical builder-derived and frozen manifests, 38 source files, zero unresolved configured-local imports, and external roots `PIL,Xlib,numpy,vizdoom`. Mutations must reject.

**C.** The A05 manifest contains 38 paths with blob identities identical to A04 at `c1d03aca16ba4d3ffcc6c63b907a6fc11a91be5d`; there are zero added, removed, or changed source blobs. This supports static closure stability over the two observed main advances.

**U.** This is static provenance only. It does not execute or import production code or establish dynamic/native dependency closure, owner identity, release timing, useful feedback, recovery, threat response, or task effect. It does not satisfy #59's live threat-exposure gate. No container, display, game, model, or input was used.

## Reproduction

From the repository root with the exact commit available as `origin/main`:

```powershell
python -B research/doom/results/map01-v39-v15-release-closure-a05-current-main-20261005/derive_current_closure.py
python -B research/doom/results/map01-v39-v15-release-closure-a05-current-main-20261005/audit_current_closure.py
```

The builder and independent verifier each require `origin/main` to match the fixed source commit. The verifier independently re-derives the AST closure and all Git blob/content hashes. `RUN_RECORD.md` records commands and mutation controls; `SHA256SUMS` binds the package.

The next runtime-level owner-selection test remains a separately frozen construction candidate. Static closure is not permission to start a live allocation.
