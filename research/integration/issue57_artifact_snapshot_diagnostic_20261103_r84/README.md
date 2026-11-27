# Immutable Calc artifact timing diagnostic r84 — 2026-11-03

## Result

**DID NOT REPRODUCE r80.** One fresh predicate-skip arm on current main passed the scoped Calc task gates. Its first immutable pre-close snapshot was already a verified 19,140-byte FODS containing A1=731 and A2=864. The 0, 100, 250, 500, and 1000 ms snapshots had the same SHA-256 43bef56bcb7cf3f9f37a12075ce4fd4a4d10c14c3154d4ceee4f8c92bfd3cbf7, unchanged inode/mtime, and each snapshot independently verified. The post-close snapshot and path-based verifier had the same hash and result.

Release was confirmed with empty keys/buttons; owner exit was 0; the exact Calc/oosplash generation exited naturally with code 0; process-group cleanup was not_needed; the call-bound parent verifier returned verified and task_success=true; container exit was 0. The compiled method's own SAFE_YIELD/effect_unavailable signal remains distinct from the parent task verifier.

## Comparison to r80-a6

The r80 pre-close verifier recorded hash b9c3744304b6f13c7804aa1ad1fe1e18384f6c53bf058975c05eae5139637d4f, identical to that attempt's registered blank-artifact hash, and found no populated cells. The retained post-run FODS now has a different hash (1b266ca140a06d315121b66ddfeb9068114d30d7590a9e212ad13bae6096ecb7) and the current byte verifier finds A1=731 and A2=864. In r80, the experiment skipped its Ctrl+Q step because no task-save request was issued after the failed pre-close verification; interface_close then used SIGTERM cleanup, so natural app exit was never tested for that arm.

r84 found the completed artifact at its first immutable snapshot and did not show a change over the fixed 1000 ms window. The contrast makes a transient write/progression delay plausible in r80, but one diagnostic replicate cannot determine its cause or attribute it to OCR. The original r80 failure remains a failure; its later file does not upgrade it.

## Scope and retained evidence

This is a one-arm diagnostic, not an efficiency comparison. It used current main a7bac319ab880637f1db9d0b8b1670b313269393, the pinned cached Docker image and package versions, no model/provider/API, and no Docker setting changes. The immutable FODS snapshots, stat brackets, each verifier result, close receipt, parent verification, preflight, invocation, preregistration, analyzer, and hashes are preserved in this directory. See analysis.json and SHA256SUMS.json.

Issue #57 remains open. This diagnostic does not establish model/provider token efficiency, broad reliability, WSLc, MAP01, or overall completion.
