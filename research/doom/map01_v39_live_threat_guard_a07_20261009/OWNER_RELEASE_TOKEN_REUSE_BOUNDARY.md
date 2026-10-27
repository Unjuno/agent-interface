# A07 owner-release reconciliation: token reuse boundary

A synthetic fixture duplicates one cancellation under a different cancellation ID while retaining the same intent token. It supplies one owner explicit key-up event. The historical `audit_a07_owner_release_reconciliation.py` counts that same owner event against both cancellations and returns `PASS_CUSTODY_RECONCILED_SCOPED` for both. Its key-count reconciliation does not establish one-to-one ownership when intent tokens are reused across cancellations.

The saved A07 raw input has not been inspected for this condition. This finding does not prove token reuse or unsafe physical input in A07, invalidate its recorded result, or establish MAP01 success. Preserve the original auditor and saved result as historical evidence. A future successor should bind release evidence to its proper operation and prevent cross-cancellation reuse, while handling terminal owner-cleanup receipts separately and reporting missing or ambiguous identity as unverified.

`python -B research/doom/map01_v39_live_threat_guard_a07_20261009/test_owner_release_token_reuse_boundary.py` exercises temporary in-memory fixtures only. It starts no game, GUI, model, input or allocation.
