# #1922 reusable receipt session-binding counterexample

Decision: **FAIL_REUSABLE_RECEIPT_SESSION_BINDING_UNSOUND**.

The analysis is bound to the retained #1900 bridge v1 blob
`b119c7c4112b9f9873264e6964883ddba5fea906`.

## Exact source defect
`store()` admits a reusable receipt using only:
- role = `PREPARED_REUSABLE_VERSIONED`;
- storage = `PERSIST_DEPENDENCY`;
- scope = `FOCUS_OBSERVATION_CURRENTNESS`;
- exact source blob.

`reusable_current()` then checks only `current`, role and storage.
`reuse_revalidate(payload)` returns `revalidated` whenever that stored receipt is current and copies the supplied payload without comparing session, canonical resource, surface identity or receipt lineage.

The source contains zero `session_id` and zero `canonical_resource` fields.

## Counterexample
A valid current focus receipt from session A is stored. A later caller reuse in unrelated session B supplies payload B. Because session/applicability identity is never compared, v1 returns `revalidated` for B.

A current=false control returns `stale`, so this is not a total currentness failure. It is specifically missing applicability/session binding.

## Consequence
#1900 must not be resumed with bridge v1 even if exact caller source transport becomes available. A successor must bind persistent receipts to an explicit canonical dependency key and caller applicability/session identity before reuse.

The original #1900 HOLD remains unchanged; this FAIL is a design successor, not a relabeling of its unexecuted formal.
