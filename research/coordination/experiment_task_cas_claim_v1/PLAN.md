# Task-keyed CAS experiment claim v1
Task: EXPERIMENT-TASK-CAS-CLAIM-20260917-001
Issue: #982
Publication base: b488c44c49059b6cf1385ecd43b32a16ce7a9fd5

H: synchronized read-then-append lets multiple contenders self-authorize for one task, while atomic creation of one deterministic task-keyed Git ref with expected-old=zero produces exactly one owner. Different task refs should not serialize globally.

T: disposable local bare Git repositories only. Primary formal = contender counts 2/4/8 x32 reps x READ_APPEND/TASK_REF_CAS =192 fresh same-task races. CAS claim objects are immutable JSON blobs {task_id,worker_id,base_sha,nonce}; ref name is refs/experiment-claims/<sha256(task_id)>. All objects/read-state prepared before one multiprocessing barrier. Different-task control =32 reps x8 unique task IDs concurrently under CAS. One formal runner invocation, reruns0. Independent auditor rehashes task keys, claim-object bytes and winner constraints without importing runner.

D: PASS iff READ_APPEND has >1 owners in all96 baseline races; CAS has exactly1 owner in all96 candidate races; every candidate loser resolves the exact final winner object and never reports ownership; different-task controls succeed8/8 x32; no winner outside contenders; source/result/audit/controls pass; formal1/reruns0.

C: local Git ref CAS is not yet proof of identical remote GitHub connector/API semantics. The baseline is intentionally adversarial and not a natural duplicate-rate estimate. Unique acquisition does not solve lease expiry/transfer/abandonment.

U: coordination primitive only; no scientific/runtime/MAP01 result and no production orchestration policy promotion.
