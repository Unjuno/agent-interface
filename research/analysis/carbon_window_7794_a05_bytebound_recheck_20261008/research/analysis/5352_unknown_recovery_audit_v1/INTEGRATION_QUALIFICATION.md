# Formal-03 archive qualification — missing RESULT.md

This package is retained as an immutable `STOP_AUDIT_SEMANTIC_MISMATCH`, not as a scientific PASS. The original 13 files in this directory are preserved byte-for-byte from Draft PR #5573, including the raw candidate/audit outputs, freeze files, and attempt history. No candidate, auditor, Docker image, or formal allocation was run during this archive.

**The referenced `results/formal-03/RESULT.md` is missing from the PR head.** `README.md` and `PACKAGE_SHA256.json` reference it, and the manifest records expected SHA-256 `f521a3a3202fc1d886d4dee08713c72204d23258060da19a553573aecde7b20e`, but exact-head tree inspection finds no such path. The latest main tree also does not contain it. No bytes were recoverable from the PR head, so this archive does not recreate or substitute that artifact. The available `REPORT.md`, `RUN.md`, candidate JSON, audit JSON, and attempt history remain the evidence actually present.

Interpret the disposition only as the recorded candidate/auditor semantic disagreement on the finite literal hysteresis simulator. It does not resolve the broader #5352 recovery-gain hypothesis or establish runtime safety. The missing file remains an explicit provenance gap.
