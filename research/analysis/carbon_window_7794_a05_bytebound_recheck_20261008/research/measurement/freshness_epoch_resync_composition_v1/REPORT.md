# Freshness-aware epoch-resync composition — first outcome

Decision: `PASS_FRESHNESS_EPOCH_RESYNC_COMPOSITION_SCOPED`.

This source-first deterministic composition holds merged #1031 freshness/capacity behavior and retained #677 epoch-resync semantics fixed. The only integration factor is applying epoch-fenced resync to an actual bounded-overflow freshness-aware stream, then continuing ordinary fresh/stale state and critical traffic in the new epoch.

## First primary outcome

Exactly one frozen primary runner invocation used seed `104020260918001` for 50,000 scenarios / 1,450,228 generated records. Every scenario first produced an actual session-A overflow and then executed one valid overflow-bound current-snapshot resync. Candidate and separately structured history-reconstruction oracle matched 50,000/50,000. Invariant errors, historical-gap mutations and cross-session errors were all zero.

All 50,000 positive resyncs entered epoch2 exactly once. Post-resync traffic generated a second active overflow in 22,293 scenarios, providing direct evidence that the retained historical gap from epoch1 remains immutable even while epoch2 independently enters a new incomplete-coverage state. Fresh newest-state replacement and stale-state suppression remain inside the same candidate/oracle equality result. `grants_input_authority=false` throughout.

Primary runner wall was 6.345 s; outer `/usr/bin/time` wall 6.99 s and max RSS 93,228 KB in this container. Diagnostic only; no performance claim.

Independent audit over the untouched RESULT returned `PASS` / `errors=[]`. RESULT SHA-256 is `80142599f65019effdc1f7ade6f7c98f78fb87b60f031b651f592d73e0d1e9be`.

## Negative / integrity controls

Fixed construction controls cover valid resync, post-resync latest-state replacement, second overflow with immutable old gap, stale snapshot, wrong overflow identity, wrong snapshot session, exact replay, no-overflow request, cross-session isolation and naive same-epoch gap laundering; 10/10 passed before primary.

Construction also exposed two pre-primary harness/API gaps: request-target session had to be separated from snapshot.session to represent wrong-scope resync; session B needed at least one pre-state row to make cross-session comparison total. Both were repaired before the primary seed was used.

Source-first GitHub readback later caught two byte mismatches (`controls.py`, `fixture.py`) before primary; both were repaired to the locally frozen bytes and the second readback matched all eight scientific blobs recorded in `FREEZE.json`.

After RESULT/AUDIT had completed, a combined five-mutation corruption wrapper exceeded the outer command budget because every mutation independently recomputes all 50,000 scenarios. The primary was not rerun. The same frozen `audit.verify` was then applied one mutation at a time; seed, digest, decision, formal invocation count and historical-gap-mutation count were all rejected 5/5. The aggregate-wrapper timeout is retained as an audit-cost limitation rather than hidden.

## Scope

This is in-memory deterministic stream semantics. It does not establish live watcher transport, persistence/restart durability, planner comprehension of `RESYNC_REQUIRED`/historical gaps, ACK/resolution, full-trace retrieval, task correctness, token savings or runtime promotion.
