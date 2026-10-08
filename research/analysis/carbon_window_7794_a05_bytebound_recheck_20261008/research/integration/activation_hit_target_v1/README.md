# Retained activation hit-target evidence (#4084)

This directory retrospectively publishes the already-consumed local allocation `activation-hit-target-20260922-01`. It is **not** GitHub preregistration and no GUI/input case was rerun for publication.

Scientific result: **PASS_ACTIVATION_HIT_TARGET_BOUNDARY_SCOPED**. This is a finite boundary result, not approval of an unconditionally safe click-to-focus recovery recipe.

The exact previously generated additive patch is stored losslessly as 13 consecutive text parts under `full_patch/`. Reconstructing those parts must produce:

- SHA-256 `00de864817f10d1b0bc24acbef1fcbdae89adbeafd5414e28a8d8545cb39efd5`
- 1,315,836 bytes
- 12,441 lines
- 280 added files
- zero modified existing files
- zero deletions

The patch itself creates the complete original `research/integration/activation_hit_target_v1/**` research tree, including readable PLAN/REPORT/source, raw case evidence, construction failures, audit and corruption controls.

The original conversation research ZIP remains separately identified by SHA-256 `a9d6b39b5f7df6ba0952008e7df424c32ff25a4307d3a5df68af94ce262099d4`.

Read-only reconstruction:

```sh
python -B reconstruct_patch.py /tmp/activation-hit-target-4036-additive.patch
git apply --check /tmp/activation-hit-target-4036-additive.patch
```

Do not rerun the consumed formal batches for review. The historical local `STOP_PUBLICATION_NO_WRITE_CAPABILITY` remains inside the original report as truthful chronology; this later delivery does not rewrite it.
