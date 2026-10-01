# #1579 Provenance-free HUMAN/process actor indistinguishability

Decision: **PASS_PROVENANCE_FREE_ACTOR_INDISTINGUISHABILITY_SCOPED**

## Result

The declared provenance-free observable space contains 384 states (3 event families × 4 effect classes × 4 timing buckets × 2 focus states × 4 changed-state digest classes). Each observable state was paired with two hidden histories differing only in producer identity: HUMAN versus EXTERNAL_PROCESS.

- observable-identical pairs: 384/384
- hidden histories: 768
- formal invocations: 1
- reruns: 0
- authority promotions: 0
- task-success promotions: 0

Every tested actor-specific deterministic heuristic (timing, event shape, focus, effect shape, composite) made exactly one hidden-truth error per indistinguishable pair: 384 errors each. This is not a property of those heuristics alone; PROOF.md establishes the general deterministic indistinguishability result for identical verifier-visible input.

The safe `UNATTRIBUTED` policy made zero false specific HUMAN/EXTERNAL_PROCESS claims. It intentionally declines to answer the hidden identity and is therefore not scored as actor-identification success.

Adding a correctly bound trusted actor witness changed the observable input and separated all 384 controls with zero witness error.

Frozen audit: PASS. Independent postformal auditor: PASS; seven copied-result corruptions were rejected 7/7.

## Scope

This result does not say physical-human attribution is impossible in principle. It says event/effect/timing/focus/state-digest fields alone cannot distinguish two hidden producers when those fields are identical. Trusted kernel/device provenance, an authenticated input broker, hardware attestation, or another independent actor witness can break the equivalence and must be measured separately.

No live human experiment, privacy inference, GUI/model/task-performance, latency, token, or production-ABI claim is made.
