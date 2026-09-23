# ROADMAP — MUTATION-ACTOR-RECEIPT-AUTHENTICITY-BATCHED-20260918-002

H: #1263 science should complete unchanged when only outer execution is partitioned into immutable global-ID batches.
T: exact #1263 source; 12 disjoint 30,000-row batches; immediate replay remains within row; aggregate checks coverage/no overlap and original gates.
D: mismatch0, forged SELF0, replay SELF0, authority/task-success0, exact [0,360000) coverage, 12/12 unique batch outputs, source integrity.
C: batching could change state only if cross-row nonce reuse existed; frozen corpus uses globally unique nonce n{i}, so no cross-batch legitimate reuse exists.
U: synthetic standard-library HMAC contract only.
STOP: no batch rerun/replacement; incomplete batch stops allocation.
