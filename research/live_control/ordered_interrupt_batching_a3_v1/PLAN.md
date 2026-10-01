# Ordered interrupt batching A3 sharded formal — #1884

Task: `EVENT-ORDERED-INTERRUPT-BATCHING-A3-SHARDED-20260919-003`

#1871 and #1876 both retained scientific NONE with zero durable rows. A3 preserves the exact batching science/corpus/gates and changes only formal execution/durability packaging: one monolithic exhaustive process becomes nine immutable disjoint shard processes.

H: an exact corpus partition can make the formal durable under the command wrapper without changing any scientific decision.

T: shard00 owns lengths0..5; shard01..08 own length6 by fixed first alphabet symbol index0..7. Total exact coverage299,593 sequences and2,054,353 prefix checks. Each shard writes once; no rerun/replacement. Aggregate only after all9 results. Independent audit re-enumerates each shard.

D: PASS iff all9 shards exist once, coverage/counts exact, sequence/identity/session/metadata errors0, directed order preserved, negative priority-sorted comparator reverses >=1 directed case, delivery reduction exists, malformed controls fail closed, and independent audit/source integrity passes.

C/U: process boundaries can change runtime but timing is not a gate. Representation-only; no model, token, latency, live watcher, ACK/retry, task-success, transport atomicity or production claim.
