# #6256 T2 — forward proposal checker and observation-cost boundary

## H / T / D / C / U

**H.** A forward-only checker that validates an authored proposal can establish whether that proposal is safe, but does not by itself derive the complete weakest admissible initial-state predicate. On the frozen #6256 finite model, a conservative checker that inspects only listed proposal states can miss a safe omitted state; an exhaustive forward checker can recover the oracle only by enumerating every state and outcome, which is extensionally equivalent to the finite oracle rather than a distinct backward-derivation benefit. Observation-cost ordering may be reported without inventing weights, but no unique cheapest cue set follows where cost dimensions are incomparable.

**T.** Allocation `BACKWARD-OBSERVABLE-GUARDS-6256-T2-COMPARATOR-20261002-01`. Read the byte-pinned T0 model and candidate from the T1 package. Construct two explicit forward-checker semantics: (A) proposal-local validation over candidate-listed states, and (B) exhaustive all-state forward enumeration. Compare their admitted sets to the exact universal preimage and authored guard. Enumerate permitted cue subsets over the verified stratum and report componentwise Pareto dominance under synthetic ordinal costs, including a control proving that changing invented weights can reverse the selected singleton. Run pure CPU, no application/model/network/action. Candidate/runtime invocations 0.

**D.** Scoped PASS only if byte identities and expected state/outcome classifications are checked, the incomplete proposal-local comparator under-approximates the oracle, exhaustive forwarding agrees extensionally while requiring full state coverage, UNKNOWN aliasing is preserved, and Pareto output is weight-free and internally verified. Any mismatch is retained as FAIL/HOLD. This does not fulfill #6256's original proposal-comparison requirement for every possible notion of forward checker, nor establish real observation cost.

**C.** A forward checker may itself be defined to enumerate the whole model and compute the exact preimage, in which case no conceptual advantage for backward calculation is demonstrated. The result depends on the frozen comparator definitions; it does not prove that #6256's broader baseline has been fairly operationalized.

**U.** All observation costs here are authored ordinal coordinates, not measured latency/tokens/error risk. No real GUI, model, user data, authority, task effect, product, or performance claim. Docker Desktop was probed but its CLI did not respond; this deterministic finite CPU audit has no external effects and proceeds on host.

## Frozen inputs / provenance

- Source allocation: #6256 T0 via #6277 / PR #6280.
- Model SHA-256: `274c4f7de76f0c68738cdb73d3683e3dc57f570ccecc6f4b67b4adc01060958d`.
- Candidate SHA-256: `266f6df83f0a824bf437ce1bb16fda0cc28abf046b4c57dd6428f727170078d4`.
- Parent audit SHA-256: `cb30cc5c2a580410c8b3eaac09fe1f8731a5c7ab87d8322e75988fb1cb11fe8f`.
- Parent T0 remains `HOLD_INCOMPLETE_MUTATION_COVERAGE`; T1 #6277 adds one missing mutation only. Neither record is edited or reclassified.

## Invocation ledger

Before formal run: candidate 0, comparator 0, cost analyses 0, post-freeze retries 0. Construction tests use toy records only. After freeze, invoke the comparator once and retain raw result plus hashes.
