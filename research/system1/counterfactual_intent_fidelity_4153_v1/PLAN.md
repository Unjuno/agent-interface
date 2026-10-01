# #4153 counterfactual intent fidelity — preformal plan

Allocation: `counterfactual-intent-fidelity-4153-20260923-01`.
Parent: #4153; lineage: #3458. Authority-neutral shadow evaluation only.

## H
A small MLP in the #3458 family that receives explicit intent context can preserve a bounded synthetic teacher's intent/effect disposition on held-out counterfactual rows where observation state is byte-identical and only intent changes. A state-only control trained on the same rows should expose the state→action shortcut when teacher dispositions differ by intent.

## T
- CPython + installed PyTorch CPU; no OS input, GUI, network, provider/model API or user data.
- Base state: six dimensionless features `(dx,dy,vx,vy,confidence,visible)`, same family used by #3458 synthetic pilots.
- Intents: `TRACK`, `STABILIZE`, `WATCH_ONLY`, `OUT_OF_SCOPE`.
- Outputs: `CONTINUE`, `CORRECT`, `WATCH`, `YIELD`.
- Teacher is deterministic and state-dependent inside TRACK/STABILIZE; WATCH_ONLY is a constrained monitor intent; OUT_OF_SCOPE always YIELD.
- Candidate input: state + four-way one-hot intent (10 dims), MLP 10→24→24→4.
- Negative control: state only (6 dims), same hidden widths and optimizer schedule, trained over the exact same contradictory counterfactual rows.
- Fixed seed 4153. Generate 4096 train base states and 2048 disjoint held-out base states; expand each across all four intents (16384 train rows / 8192 held-out rows). One formal fit per arm, no retry/tuning/replacement.
- Extra invalid-intent controls are external fail-closed checks and never enter training.

## D
`PASS_COUNTERFACTUAL_INTENT_FIDELITY_SCOPED` only if all are true:
1. candidate held-out semantic accuracy >= 0.97;
2. candidate exact-all-intents-per-base rate >= 0.90;
3. candidate accuracy on teacher-disagreeing same-state intent rows >= 0.96;
4. candidate OUT_OF_SCOPE YIELD recall >= 0.995;
5. candidate action-on-teacher-YIELD error <= 0.01;
6. candidate forbidden-effect proposal rate <= 0.01;
7. invalid/unknown intent IDs fail closed to YIELD 100%;
8. state-only baseline exact-all-intents-per-base <= 0.60, establishing the intended shortcut discriminator;
9. independent audit recomputes metrics from retained predictions and rejects >=8 copied-evidence corruptions.

`FAIL_STATE_ACTION_SHORTCUT` if the intent-aware candidate misses gates 1–6 while the state-only baseline remains substantially invariant/ambiguous on differing-intent rows. `FAIL_INTENT_SCOPE_YIELD` on candidate OOS/invalid-intent gate failure. `HOLD_REPRESENTATION_ALIASES_INTENT` if even the deterministic teacher produces <50% base states with at least two distinct dispositions. Missing source/process/result/audit evidence is STOP/HOLD.

## C
The synthetic intent one-hot may be easier than natural-language Astra intent. The state-only baseline receives contradictory labels by construction. Candidate improvement therefore demonstrates conditioning capacity for this bounded representation, not broad semantic understanding or task utility.

## U
No Astra supervision, images, GUI, live authority, task effect, cross-app transfer, online adaptation, natural intent distribution, or production claim. This does not rehabilitate prior #3458 boundary/shift failures. Latency is not a decision gate in this rung.
