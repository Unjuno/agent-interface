# Freshness-aware bounded critical retention composition — first outcome

Decision: `PASS_FRESHNESS_BOUNDED_CRITICAL_COMPOSITION_SCOPED`.

This source-first deterministic composition adds only the #665-style per-session critical capacity/overflow boundary to the exact #1021 freshness semantics. The critical allowlist, stale/fresh threshold, `{session,target,stream}` state scope, source ordering and no-authority role are unchanged.

## First primary outcome

Exactly one frozen primary runner invocation used seed `103120260918001` for 75,000 batches / 1,535,166 records. Candidate and separately structured oracle matched 75,000/75,000. Invariant errors were zero. The corpus contained 690,827 critical records: 613,258 retained critical payloads and 77,569 explicitly unretained critical records, giving critical accounting error zero. Overflow occurred in 28,268 batches / 41,629 session instances. Every overflow uses `RESYNC_REQUIRED` and preserves the first-unretained event identity/sequence/kind plus exact unretained count. `grants_input_authority=false` throughout.

Primary runner wall was 13.981 s; outer `/usr/bin/time` reported 14.61 s and max RSS 93,356 KB in this container. These are diagnostic only, not a performance claim.

Independent audit over the untouched result returned `PASS` with `errors=[]`.

## Integrity history

Before the primary seed was used, source-first GitHub readback found `fixture.py` and `runner.py` did not match the Git blobs recorded in the freeze manifest. The mismatch was repaired to the frozen local bytes and a second readback matched all nine scientific file identities. Primary remained 0 before that repair.

The combined shell command later hit its outer execution limit only after the primary RESULT and independent AUDIT had both completed. Inspection proved the primary had already closed and no process remained. The timeout occurred during the frozen corruption wrapper, which recomputes the full 75k audit once per mutation. The primary was never rerun. Five corruption mutations were therefore checked one-at-a-time through the same frozen `audit.verify`; all 5/5 were rejected (seed, digest, critical count, decision, formal invocation count). The aggregate wrapper timeout is retained as an audit-harness cost limitation, not hidden.

## Scope

This is queue/observation semantics only. It does not establish completeness of the authored critical-kind allowlist, planner handling of `RESYNC_REQUIRED`, epoch resync correctness (#677), persistence, model/token savings, task benefit or live watcher behavior.
