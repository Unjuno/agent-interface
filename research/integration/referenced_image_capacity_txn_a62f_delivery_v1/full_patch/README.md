# Lossless full-evidence patch for #4093

This directory is a transport wrapper for the original, already executed allocation. It does **not** rerun the experiment.

The 28 numbered files are consecutive line ranges from the exact original `agent-interface-capacity-additive.patch`, which is a `git diff --binary` additive patch containing all 1,089 research files, including binary PNG/SQLite evidence.

Expected reconstructed identity:

- bytes: `10,307,800`
- lines: `137,002`
- SHA-256: `3680d951516519da72f545be389f28e2a8648b8c5b8dfd571e138fdcbf8d5d42`
- existing files modified: `0`
- deleted files: `0`

Reconstruct without executing scientific code:

```sh
python -B reconstruct_patch.py /tmp/agent-interface-capacity-additive.patch
git apply --check /tmp/agent-interface-capacity-additive.patch
```

Applying the patch creates `research/integration/referenced_image_capacity_txn_a62f_v1/**`. The retained formal allocation is consumed; do not rerun it merely to review publication.

The historical `PUBLICATION_STATUS.md` remains unchanged as the truthful record of the earlier connector publication STOP. This full-patch delivery is a later publication repair under the same Issue, consistent with `docs/ISSUE_FAILURE_CLASSIFICATION.md`.
