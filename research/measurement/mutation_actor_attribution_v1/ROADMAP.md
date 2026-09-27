# ROADMAP — MUTATION-ACTOR-ATTRIBUTION-CONTRACT-20260918-001

## H
Temporal proximity alone will falsely credit non-self mutations to the current intent, while exact lineage-bound attribution over session/intent/action/target/delta plus causal ordering will match an independent history-replay oracle with zero false self-credit.

## T
1. Freeze candidate/oracle semantics and malformed/conflict handling.
2. Construction only on excluded control IDs.
3. Freeze source hashes before formal.
4. One formal invocation: fixed controls + >=300,000 seeded records, balanced strata.
5. Compare candidate/oracle state+actor+invalidation; separately count TEMPORAL_NEAREST false self-credit.
6. Independent auditor reconstructs expectations from raw records without importing candidate classifications.
7. Corruption controls mutate lineage/evidence and must reject.

## D
PASS only if candidate/oracle mismatches=0, LINEAGE_BOUND false-self-credit=0, all exact self lineages SELF_CONFIRMED, explicit external witnesses EXTERNAL_CONFIRMED with exact actor class, unknown/conflict/mismatch UNATTRIBUTED, no mutation NO_MUTATION, invalidation recommendation correct, authority/task-success promotions=0, TEMPORAL_NEAREST false-self-credit>0, integrity/audit/corruption pass.

## C
The result may validate only evidence-flow semantics; it does not prove real external actor detection or spoof resistance.

## U
Synthetic standard-library contract experiment only; no real GUI, human, OS, network, model, task success, or authority claim.

## Stop
One formal invocation. No threshold tuning, rerun, replacement, or rescue in this allocation.
