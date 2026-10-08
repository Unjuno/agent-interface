# O4 local VERIFY escalation contract — R0

Task: `OBSERVATION-GATING-O4-LOCAL-VERIFY-ESCALATION-R0-20260918-001`

## H
A local verifier may safely avoid a model escalation only when its receipt is current-observation-bound, intent-bound, explicitly non-authoritative, and resolves a tri-state predicate to TRUE or FALSE. UNKNOWN, stale observation, intent mismatch, missing receipt, or attempted authority escalation must escalate. A comparator that trusts TRUE/FALSE without currentness/lineage will suppress necessary escalation on nontrivial cases.

## T
Standard-library Python only. Directed cases plus a deterministic randomized corpus of 250,000 rows with fixed seed 164720260918001 across CURRENT_TRUE, CURRENT_FALSE, UNKNOWN, STALE, INTENT_MISMATCH, MISSING and AUTHORITY_FORGED. Candidate is compared to an independently structured admissibility oracle. A naive lineage-blind comparator is retained only as a discriminator. Independent audit checks counts/decision and four copied-result corruptions.

Construction is excluded. After source freeze/readback, run exactly one formal invocation from the frozen source with reruns/replacements/tuning0.

## D
`PASS_O4_LOCAL_VERIFY_ESCALATION_CONTRACT_SCOPED` iff candidate/oracle mismatch0, every directed case matches, local resolution occurs exactly for current TRUE/FALSE receipts, all other classes escalate, naive unsafe suppressions >0, independent audit passes, and source/result integrity closes. Any stale/intent/authority case resolved locally is FAIL. No naive discriminator is HOLD.

## C
This tests escalation-contract semantics, not whether a real verifier is accurate or cheap. TRUE/FALSE labels are only as good as their domain predicate. A production verifier also needs source-specific evidence/currentness and must not convert verification into input authority.

## U
Synthetic state-machine contract only; no GUI/model/token/latency/task-success or production claim. A PASS permits a real retained-evidence or live O4 transfer rung, not marking the broad ROADMAP O4 complete by itself.
