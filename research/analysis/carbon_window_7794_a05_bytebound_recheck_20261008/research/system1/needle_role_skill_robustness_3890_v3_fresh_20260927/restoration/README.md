# Issue #4580 evidence restoration

This additive package restores the ten lossless seed ZIPs named by the existing `outputs/formal01/bundles/EVIDENCE_MANIFEST.json`. It does not rerun the candidate, optimizer, or loader and does not change the original result or its scope.

`restoration_snapshot/` preserves the exact frozen source bytes referenced by the original `FREEZE.json`; its nested `.gitattributes` disables line-ending conversion so the source snapshot remains byte-stable in Git. This is necessary because the current-main transplant's files at the original experiment paths do not hash to the original execution freeze.

From the repository root, run:

```powershell
py -3.11 research/system1/needle_role_skill_robustness_3890_v3_fresh_20260927/restoration/verify_restore.py
```

The script validates every archive against the committed manifest, restores all members into a temporary directory, invokes the retained post-run auditor from `restoration_snapshot/`, and writes `outputs/formal01/RESTORE_AUDIT.json`. It performs no network or container operation and writes no restored raw files outside its temporary directory. The audit result is limited to the original synthetic allocation.
