# Action-grounded visual memory v1

## Question

Can a small target crop retain enough verifiable provenance to be reconsidered
under a later condition without confusing archived success with current input or
semantic authority?

## Contract

`action_grounded_visual_memory_v1.py` binds one exact crop to:

- the task, environment, retained evidence-session identity, surface and exact
  source observation;
- the target handle, point, crop box and RGB patch hash;
- the admitted action ID/program hash and its completed, empty verified release;
- the first successful semantic effect, exact artifact reconciliation and
  independently scored output;
- the full local/model recovery trace, call identities and measured model wait.

Retrieval fails closed on task, environment, session, surface, target-name or
current-exactness mismatch. Even a matching receipt returns only
`ELIGIBLE_VISUAL_REFERENCE`: the current target must be revalidated and any new
input requires fresh admission. Artifact verification says only that archived
bytes still match the receipt.

## Retrospective application

The derivation script was applied once to the already frozen adaptive semantic
repair v2 run. It produced two 42x18 crops:

| Source route | Repair calls | Retained provenance |
|---|---:|---|
| resize -> local repair | 0 | exact source 13, admitted submit, exact successful effect 15, independent output |
| hover -> model reacquisition | 1 | exact source 19, admitted submit, exact successful effect 21, independent output |

The two target hashes differ, which preserves the actual hover mutation rather
than relabeling it. Ten contract tests and an independent retained audit pass.

## Meaning and limits

This is an offline provenance result derived from one prior live run. It makes a
failed or successful visual idea reproducibly addressable under another condition;
it does not show that presenting the crop improves a model. There were no new
model calls, input actions or latency/token measurements. The next allocation
should preregister a held-out, same-model/task/environment comparison of current
frame plus this action-grounded crop, current plus prior full frame, and current
with no prior visual memory. Correctness, wrong-target actions, actual input
tokens, images, fallback, and recovery time remain the decision metrics.

The evidence-session IDs are deterministic labels for these two retained case
directories; the runtime did not authenticate or emit a session credential.
