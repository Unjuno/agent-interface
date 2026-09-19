# #1848 role-bound mediated-ledger lifetime

## H
`PREPARED_REUSABLE_VERSIONED` receipts may enter persistent dependency storage and remain reusable only while versions remain current. `FRESH_COMMIT_BOUND_CURRENT` receipts are exact-intent/exact-commit ephemeral evidence and must never enter the reusable cache.

Persisting both roles in a generic cache lets an old TRUE commit gate substitute for fresh current evidence after its truth, lineage, intent, or commit epoch changes.

## T
Exhaustive standard-library ledger/cache state machine over 96 later-use states:
- dependency current/stale;
- current gate truth FALSE/UNKNOWN/TRUE;
- current gate lineage current/stale;
- intent match/mismatch;
- commit epoch match/mismatch;
- fresh gate present/absent.

A positive old commit gate exists before the later use. Compare ROLE_BOUND against GENERIC_CACHE. Also test storage policy for reusable, commit-bound, and unknown roles. One source-frozen formal invocation.

## D
PASS iff ROLE_BOUND/oracle mismatch0, unsafe0, false-reject0; reusable dependency persists and same-version reuse remains possible; changed version cannot authorize; persistent commit receipt count0; cross-intent/cross-epoch replay accepts0; GENERIC_CACHE persists the old gate and exposes >0 unsafe replay admissions; unknown role rejects; audit/source/invocation integrity pass.

## C
Separate storage tables/types are acceptable. A one-shot flag without intent/epoch binding is not sufficient if a duplicate receipt can be replayed.

## U
Deterministic storage/replay mechanics only; no GUI/model/input/latency claim.
