# Original PR #7849 archival qualification

The nine original smoke-package blobs and six contemporaneous runtime/test/documentation blobs are retained unchanged from PR #7849 head ef190e1037ff2f9df0cb2e941578a79a9fe0019b. Runtime snapshots under historical-7849 are archival text, not current main implementation. The first-launch STOP and subsequent one-shot result remain distinct; no input was replayed.

The frozen SHA256SUMS verifies .gitattributes against the stored Git blob. Five entries (COMMANDS.txt, probe.py, README.md, result.json and STOP_FIRST_LAUNCH.md) match only if the stored LF blob is converted to CRLF. audit.py and PLAN.md match neither the stored blob nor the tested simple LF-to-CRLF conversion. Therefore the source PR's statement that all package checksums verified is not independently established for these published blobs. Preserve the original manifest and result, and treat the checksum discrepancy as unresolved rather than changing the reported historical outcome.

The saved result describes one direct-backend Windows fixture sample, not application delivery, hardware key state, MAP01, current-main behavior, or general reliability. #7849's current runtime integration remains separate.
