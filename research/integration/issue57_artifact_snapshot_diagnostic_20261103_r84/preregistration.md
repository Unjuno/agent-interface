# Preregistration: immutable Calc artifact timing diagnostic r84

Date: 2026-11-03. One fresh skip-condition Calc arm on current main. This diagnostic follows the r80-a6 retained-byte discrepancy; it is not an efficiency comparison and not a retry of r80.

## Question

At what point does the server-owned task-artifact.fods transition from the blank artifact to a verified A1=731/A2=864 artifact? Does the exact byte snapshot read at the pre-close verifier boundary differ from later stability or post-close snapshots?

## Frozen arm and observations

- One arm: r84-a8, predicate-scoped Entry OCR skip with normal OCR retained for cell-dependent Save guards.
- One fresh Calc process and one disposable container; no retries/replacements. Keep all failed and UNKNOWN outcomes.
- At the original pre-close verification point, read the artifact once through an O_NOFOLLOW regular-file descriptor, retain those exact bytes, SHA-256, size, descriptor/path stat identity before and after, and pass those exact bytes to verify_saved_fods_bytes.
- Repeat the same immutable byte snapshot at fixed offsets 0, 100, 250, 500, and 1000 ms from the first snapshot. Save each raw FODS and verifier result. Do not let later snapshots replace the first snapshot's gate.
- Record a normal path-based verifier result after the bounded sample series, then separately retain and verify a post-close snapshot and normal path result.
- Preserve the normal task effect, key/button release, graceful Ctrl+Q behavior, exact-generation natural-exit and parent-verifier gates. A later valid file cannot upgrade a failed first snapshot or UNKNOWN original task result.

## Frozen environment and limits

Use current main commit a7bac319ab880637f1db9d0b8b1670b313269393, pinned cached image agent-interface-xvfb-mcp:late-input-r19, Engine 29.8.1, LibreOffice 4:7.4.7-1+deb12u14, Tesseract 5.3.0-2, Xvfb 1280x800, same OCR crop/PSM/whitelist/confidence, and per-container 2 CPU / 4 GiB memory+swap / 256 PIDs / local logging / 600 s timeout. No model/provider/API, no WSLc, no MAP01, and no Docker setting changes.

## Diagnostic classification

- Write-timing evidence: first snapshot is blank/mismatched and a later bounded or post-close snapshot changes to the exact verified artifact.
- Verifier/path discrepancy: first retained bytes verify exactly while the path-based result at the same recorded boundary differs, with stable descriptor/path identity.
- Persistent task-effect failure: snapshots remain invalid or task save request is absent.
- Task effect remains UNKNOWN: any required release, exact-generation natural-exit, or call-bound parent-verification gate is missing, regardless of later file contents.

This one local diagnostic does not prove OCR causality, general reliability, model-token efficiency, MAP01, WSLc, or completion of Issue #57.
