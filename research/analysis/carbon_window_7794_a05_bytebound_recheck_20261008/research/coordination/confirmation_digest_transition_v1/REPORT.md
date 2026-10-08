# Confirmation identity bound canonical CAS

Task: `COORD-CONFIRMATION-DIGEST-CAS-20260916-016`

Decision: **`PASS_CONFIRMATION_IDENTITY_BOUND_CANONICAL_CAS_SCOPED`**

## Question

After membership and generation share one canonical GitHub content-CAS record, can an old confirmation decision still advance generation if confirmation state changes after validation? The candidate binds confirmation identity as `(semantic_content_id, revision)` in that same canonical record.

## Frozen result

| Arm | Intervening confirmation change | Old generation transition | Final generation |
|---|---|---|---:|
| unbound changed content | separate confirmation becomes B=`UNKNOWN`, rev2 | **succeeds** because canonical SHA is unchanged | 2 |
| bound changed content | canonical identity changes to new content-id/rev2 | old canonical SHA -> **HTTP 409** | 1 |
| bound same content/new revision | content-id unchanged, canonical confirmation revision 1->2 | old canonical SHA -> **HTTP 409** | 1 |
| bound stable | none | current canonical SHA succeeds | 2 |

Measured successful state updates: 5. Old-decision generation attempts: 3. One succeeds in the unbound negative control; two candidate attempts receive 409. Candidate post-409 readbacks: 2. Fresh-SHA retries after stale decisions: 0.

## Interpretation

A separate confirmation record leaves another cross-file freshness gap: changing confirmation after validation does not alter the canonical membership+generation SHA, so an old decision can still commit. Binding the exact confirmation identity to the same canonical CAS record makes a changed confirmation mutate the CAS identity and invalidates the old transition.

The same-content/new-revision control matters: a semantic content digest alone is not sufficient to distinguish a newer confirmation instance. The revision component changed the canonical record even while `semantic_content_id` stayed identical, so the old transition was rejected.

## Evidence boundary

This is sequential GitHub-backed fixture evidence. It does not establish simultaneous-request linearizability, who may author confirmation changes, crash recovery, distributed consensus, quorum availability, or external-effect safety. The candidate also requires confirmation identity changes to be represented in the canonical CAS record; a separate authoritative confirmation system that can change without updating that record would reintroduce the gap.

`verify.py` is retained deterministic checking code; no independent execution is claimed.

## Next single question

Keep the canonical membership+generation+confirmation identity record fixed. Test **one-use transition consumption**: after a generation transition commits, can an identical old confirmation identity be reused to authorize a second distinct transition/effect? Bind a transition nonce/sequence to the canonical record and compare reusable versus consumed transition identity without adding timeouts, quorum rules, or external effects in the same rung.
