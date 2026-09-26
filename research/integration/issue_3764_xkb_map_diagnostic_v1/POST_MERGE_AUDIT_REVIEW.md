# Post-merge audit of the published Issue #3764 bundle — HOLD

## H / T / D / C / U

**H** — Check whether the formal-01 diagnostic and its stored independent PASS audit remain reproducible from the exact evidence tree merged by PR #3776.

**T** — Re-run only the frozen read-only auditor in its pinned `linux/arm64` image. Mount current committed evidence and source read-only, use a separate empty temporary output directory, and do not invoke the formal Xvfb runner or modify formal evidence.

**D** — The committed `formal-01/raw.json` still hashes to `45a7cb25a9854b5ccee6ffbd712e1ade381fb25f5f1041657eec0fac3c7d7604`. The auditor rederived the same four row summaries: all three German rows show server/client map change and fresh-client agreement; the US control remains unchanged. However, the auditor returns `FAIL_AUDIT` with `ARTIFACT_INVENTORY` and `CASE_INVENTORY` for all four cases. The exact missing paths are `formal-01/cases/de-01/xvfb.log`, `de-02/xvfb.log`, `de-03/xvfb.log`, and `us-control/xvfb.log`. Their expected hashes remain in the frozen `raw.json`: `b987a262609a3720f450ab6815ed90b2069dd47b7b012959ca19c325aebf5d55` for each German row and `f172a1b0f5cf2a0d462c51dfc335af1a1dfc8e873cb66f61d018c8b1b35fe416` for the control. Repository `.gitignore` excludes `*.log`, and these bytes are absent from the published tree. The prior `AUDIT_REPORT.md`/`audit-01/audit.json` PASS is unchanged; that PASS reflects an earlier artifact tree which included the logs and is not reproducible from the committed bundle.

**C** — This is a post-merge audit of stored evidence, not a new diagnostic allocation. No Xvfb server, XKB change, XTEST, candidate backend, application, or user input was run. The image and scope are the same as the original auditor; only the exact committed evidence tree differs from the earlier audited tree.

**U / disposition** — The measurement rows remain as recorded, but the published evidence package is `HOLD_COMMITTED_ARTIFACT_TREE_INCOMPLETE`. The missing non-empty log bytes cannot be recovered from their hashes alone. Do not synthesize replacement logs, modify the original raw/audit files, or rerun the spent allocation. Recover the exact bytes from a trusted original artifact source if one exists; otherwise keep this HOLD and use a separately preregistered successor for any new diagnostic.
