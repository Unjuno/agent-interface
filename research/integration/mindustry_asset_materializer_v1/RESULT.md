# Mindustry offline asset materializer v1 — retained first outcome

Task `MINDUSTRY-ASSET-MATERIALIZER-20260917-001`, Issue #887, base `7b5287d9657df74a8b9eb230198a3d9eae752d62`.

Disposition: **`FAIL_MINDUSTRY_ASSET_MATERIALIZER_MECHANICS`**.

The source-first frozen formal runner was invoked exactly once; formal reruns are zero. The correct tiny-fixture staging path copied and verified both files and wrote an exact `ASSETS_READY` manifest. Wrong-JAR, wrong-save-after-first-copy and preexisting-output controls failed closed. However the first outcome exposed two defects:

1. **semantic implementation defect:** `materialize()` called `Path.resolve(strict=False)` on each source before `lstat`, so a source symlink was converted to its target path and the intended symlink rejection was bypassed. The `symlink_jar` control therefore published a final directory and `symlink_rejected_clean=false`.
2. **formal harness defect:** the expected sorted filename list placed lowercase `canonical.msav` before uppercase `Mindustry-v160.2-complete.jar`, while Python's actual lexical sort returns `MANIFEST.json`, `Mindustry-v160.2-complete.jar`, `canonical.msav`. The published bytes themselves were exact; only this gate was wrong.

The independent auditor correctly does not certify the failed allocation (`passed=false`). Four post-result corruption mutations are all rejected, but this does not convert the baseline failure into a pass.

## Preserved evidence

- source-first freeze commit: `af374acc5bb149d514dd8be2c0fa078a8948bc04`;
- formal invocation: 1; reruns: 0;
- RESULT SHA-256: `df6ae4819dfb6bf9d1c7c879af444d777409d06978822d78982880dd67b67d88`;
- AUDIT SHA-256: `d1180e76093a0ca749047afcbd91abe66cebaa2bf792fe8b4f6f3e3c9accc8ac`;
- CORRUPTION SHA-256: `d4822e76ba1210b5371a2004533aaa2050f0a6700d69fe8e9429a50c9cba267c`.

## Boundary / successor

Do not rerun v1. A successor may make exactly one semantic change: preserve the caller-supplied source path through `lstat`/`O_NOFOLLOW` rather than resolving symlinks first. Its formal harness must also correct the deterministic filename-order assertion. No real Mindustry JAR/save, GUI, model or live claim follows from either study.
