# #1900 caller role-receipt bridge

## H
The unchanged adaptive acquisition caller v3 can consume role-bound real-source receipts through a narrow bridge: persistent reusable dependency evidence is checked only at reuse_revalidate, while fresh commit-bound target evidence is bound to the current intent+commit epoch and consumed only at final_revalidate. Execute is reached iff both layers are valid.

## T
Model-free reuse-route transcripts over the exact main adaptive_acquisition_caller_v3 blob. Additive bridge only. Scenarios: exact positive; stale dependency; fresh FALSE gate; missing gate; prior-epoch TRUE replay; wrong-intent TRUE; commit receipt offered to persistent store; unknown role. Paired control reuses one dependency across two commits while requiring a new gate. No repair/model stages, GUI, input backend, or shared caller mutation.

## D
PASS iff positive reaches TASK_SUCCEEDED and execute exactly once; all seven negatives execute zero and input_authority none; stale dependency stops before final_revalidate; gate negatives stop at/before final_revalidate; persistent commit receipts=0; cross-intent/cross-epoch replay accepts=0; paired control reuses dependency but cannot reuse commit gate; exact caller/source/audit integrity pass; formal1/reruns0/replacements0/tuning0.

## C
Authored bridge transcript only. Binding at ingestion cannot upgrade stale lineage/currentness. No real GUI efficacy/latency claim.

## U
Scoped caller-composition mechanics only. Next discriminator after PASS is a real/retained caller source producing the same envelope at actual reuse/final-revalidation boundaries.
