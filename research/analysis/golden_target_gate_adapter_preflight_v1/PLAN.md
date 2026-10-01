# #1868 golden desktop target-gate adapter preflight

## H
The promoted golden desktop v3 retained runtime event schema can be normalized directly into #1858 commit-bound target receipts without modifying shared runtime.

Only `target_handle_checked` and `target_handle_revalidated` are commit-gate candidates. VALID+eligible maps TRUE; MISSING+not-eligible maps FALSE. Receipts retain source blob, handle and exact observation/sequence lineage and are always `FRESH_COMMIT_BOUND_CURRENT / TARGET_HANDLE_CURRENTNESS / EPHEMERAL_ONLY`.

Mint events remain observational reference creation and are never commit gates.

## T
Read-only standard-library formal over a mechanically extracted fixture from exact runtime events blob `e74b2c4021063193d858b35dd0c5ecc782a8bd74`. Fixture retains all checked/revalidated candidates with source indices plus the stale-refusal boundary from old-A MISSING through fresh-B mint. Independent auditor recomputes schema/count/boundary invariants without importing adapter code. One source-frozen formal invocation.

## D
PASS iff candidates41; checked VALID28, revalidated VALID12, checked MISSING1; invalid authority/session-alias/private-ID/lineage counts0; normalized persistent receipts0; exactly one FALSE receipt is persistent_a_field@77; mint events emit no commit receipt; old-A pointer/revalidation admissions between FALSE and B mint0; source/audit/invocation integrity pass.

## C
One retained promoted runtime trace only; future schema changes require revalidation.

## U
Compatibility preflight only; no new GUI/model/input/latency/runtime mutation.
