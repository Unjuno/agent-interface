# Preservation qualification — Issue #5922 invalidated T0

This additive note records a read-only review of the evidence originally retained at PR #5930 head `36987a032fb0ada7487d620e6c18f564321e5542`. All nine original files remain byte-for-byte unchanged; `RETAINED_BLOB_INVENTORY.json` records their Git blob identities, byte lengths and SHA-256 values. All six `SHA256SUMS` entries match. The five source files in freeze commit `5cd7cce871a99e1b1e52dc6356f7f1fe1be8cc09` retain the same Git identities. No candidate, auditor or construction suite was rerun for this preservation review.

## Permanent formal disposition

`HOLD_FORMAL_RUN_INVALIDATED` remains the sole formal disposition. Candidate invocation 1 exited zero but its exact stdout was not retained. Auditor invocation 1 failed because `candidate_output.json` was missing. Candidate invocation 2 was a recovery mistake, and its 24-row output is retained explicitly as `candidate_output_invalidated.json`. The auditor was not rerun. There are zero valid audited candidate results; the 7/7 construction result is not a formal pass.

No further candidate/auditor run is authorized under the consumed allocation. Repository CI, byte verification, JSON validity, or navigation repair cannot repair the missing first stdout or make the invalidated rerun valid. This archive establishes no rendered accessibility, WCAG, assistive-technology, human-benefit, production-route or model result.

The earlier Issue #5922 `STOP_CONTAINER_RESOURCE_AND_MOUNT_GATE` record uses a different fixture/path and reported 5/5 construction checks. It is separate from this package's missing-stdout/invalidation history; neither record supersedes the other. Prospective dynamic-setting, concurrent-input and coordinate-space ideas do not reopen either consumed allocation.

## Owner's integration gate

The [owner's status review](https://github.com/Unjuno/agent-interface/issues/5922#issuecomment-5942977230) requires this PR to remain Draft unmerged until independent local index/replay-equivalent validation and current-main sync are completed. The historical Analysis Index failure and later cancelled replay-gate remain part of the record. Satisfying those repository-maintenance conditions permits consideration of preservation only and does not change the scientific invalidation.
