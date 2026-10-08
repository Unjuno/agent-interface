# Geometric-scaffold retained identifiability v1

Issue #1559. Parent idea #1528.

## Decision

**HOLD_NO_RETAINED_GEOMETRIC_SCAFFOLD_CONTRAST**

This retained-data audit does not test whether a coarse geometric scaffold helps Astra. It tests only whether the current repository contains auditable retained evidence that isolates scaffold presence as a one-factor model-facing contrast.

## Frozen corpus

- exact main: `a1e6ca9c761c0db95a11af2807fbcce83e3638ee`
- exact tree: `86fb6601381023a5cb2d716889a70650b43f6046`
- GitHub code-search snapshot: `f4d2f1ac227c8f7b560fb88461c6a351f26ebce9`
- snapshot to exact main: 6 commits / 28 added files
- indexed `model_image` files: 98
- indexed `temporal-sheet` files: 266
- indexed explicit scaffold vocabulary hits: 0
- exact-main delta files scanned directly: 28/28
- delta explicit scaffold vocabulary hits: 0
- valid matched one-factor scaffold pairs: 0

The stale code-search index is not treated as current-main evidence by itself. All files added after that indexed snapshot were fetched from the exact main commit and scanned separately; none introduced `model_image`, `temporal-sheet`, or the frozen scaffold vocabulary.

## Interpretation

The repository has extensive model-facing image and temporal-sheet evidence, but there is no retained explicit metadata identifying a source-matched geometric-scaffold arm and no matched pair that holds task/fixture/current RGB/history/model/effort/prompt contract fixed while changing scaffold presence only.

Therefore #1528's incremental model-facing benefit is **not identifiable from retained auditable evidence**. This is not evidence that geometric scaffolds are ineffective, nor proof that an unnamed image never contained geometric structure.

## Next legal rung

A fresh A/B should use identical underlying current RGB/history, model, effort, prompt contract and independent outcome scorer. The only representation factor should be whether a separately labelled coarse scaffold is included. Do not reinterpret unrelated temporal-sheet runs as scaffold evidence.
