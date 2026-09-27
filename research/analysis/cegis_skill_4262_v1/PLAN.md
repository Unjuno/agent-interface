# Counterexample-guided skill synthesis — Issue #4262 first rung

Allocation: `cegis-skill-4262-20260923-01`.

## H
With one fixed typed skill grammar and immutable oracle, counterexample-guided resynthesis can reach the frozen contract within the rule/round budget and improve held-out correctness over the same one-shot synthesizer trained only on initial positive demonstrations, while preserving every accumulated counterexample.

## T
Finite six-Boolean state universe: `target_ok`, `evidence`, `alt_ok`, `forbidden`, `current`, `ambiguous`. Outputs are `ACT_PRIMARY`, `ACT_ALT`, `YIELD`. The fixed grammar has six named single-literal rules: forbidden-YIELD, stale-YIELD, ambiguous-YIELD, missing-evidence-YIELD, primary action, alternate action; default is YIELD. Candidate synthesis exhaustively searches all rule permutations by increasing length and chooses the first exact fit.

Initial demos are state IDs 18,19,22. Held-out states are frozen by `(3*state_id+59) mod 64 < 16`; the other states are verifier states. ONE_SHOT synthesizes once from the three demos. CEGIS uses the same synthesizer and adds only the lowest-ID verifier mismatch each round. Max 6 counterexamples and max 6 rules. One formal invocation after public source/hash freeze; no retry/replacement/tuning.

## D
`PASS_CEGIS_SKILL_SYNTHESIS_SCOPED` requires: verifier reaches zero mismatches within <=6 counterexamples and <=6 rules; every accumulated counterexample remains correct; CEGIS held-out accuracy is 16/16 and strictly above ONE_SHOT; CEGIS has zero action on oracle-YIELD states (including forbidden, stale, ambiguous, missing-evidence); alternate-valid and primary-valid states remain reachable; invalid/no-target states YIELD; authority remains none; independent raw audit errors=[] and >=10 coherent evidence corruptions reject.

If ONE_SHOT is already sufficient, retain the Issue's triviality class. Any counterexample regression or unsafe act is FAIL. Budget exhaustion is FAIL/HOLD per Issue. Missing source/raw/audit evidence is STOP/HOLD.

## C
The grammar already contains the semantic concepts required by the oracle. CEGIS discovers a safe composition/order of available rules, not new predicates. The finite verifier is not a real GUI/environment distribution.

## U
No model/provider, GUI/OS input, network experiment, latency/token benefit, learned-policy generality, runtime promotion or product claim. Synthesized skills remain authority-neutral evidence.
