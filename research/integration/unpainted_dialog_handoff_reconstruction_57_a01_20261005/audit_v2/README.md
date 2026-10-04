# A01 retained replay integrity audit v2

This additive offline audit checks whether each retained primary review receipt is joined to the exact reply and image returned to the caller, and whether the host event journal records that same reply and attribution. It reuses the committed A01/A02 replay captures and preserves the original `REPLAY_AUDIT.json` unchanged.

The v2 checker verifies the parent `REPLAY_SHA256SUMS`, the retained baseline result, all eight review-to-reply digests, embedded call/source metadata, the review and availability-event relay IDs against the returned reply ID, review image MIME type and decoded image digest, and matching `reply_available`, `presentation_started`, `presentation_callbacks_completed`, and `review_recorded` events. Every presentation event is bound to the exact returned reply digest. It writes its result to `RESULT.json` in this directory.

Run from the repository root:

```powershell
python research/integration/unpainted_dialog_handoff_reconstruction_57_a01_20261005/audit_v2/audit_replay_v2.py
python -m unittest research.integration.unpainted_dialog_handoff_reconstruction_57_a01_20261005.audit_v2.test_review_receipt_bindings -v
```

The baseline replay auditor is not rerun by v2 because its committed source checksum depends on checkout line endings. V2 independently verifies the committed raw replay hashes (normalizing only CRLF introduced by `core.autocrlf`) and leaves all original evidence and results untouched. Regression fixtures demonstrate that v1 accepts a detached review digest after the raw manifest is recomputed, while v2 rejects it; v2 also rejects matching but incorrect receipt/event relay IDs and a detached `presentation_started` digest. An unchanged retained replay is the positive control.

This is an integrity audit of retained replay artifacts. It does not establish live GUI behavior, perception quality, model/provider performance, causal benefit, or task success.
