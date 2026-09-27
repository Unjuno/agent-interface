# Tiny predicate specialist — Issue #4218

Allocation: `tiny-predicate-specialist-4218-20260923-01`
Base main: `c79f70a93d603748b155449016581dd7b9aac205`
Parent evidence: #4215 `PASS_SEMANTIC_PREDICATE_FABRIC_SCOPED`; parent files remain unchanged.

## H
A 32-support specialist for `TARGET_CORRECT` can preserve TRUE/FALSE/UNKNOWN and downstream graph semantics on held-out nuisance shifts while materially reducing evaluation cost versus the exact frozen #4215 six-predicate batch backend.

## T
Stdlib CPython only. Support set: exactly 32 authored rows, 8 per target evidence pair `(1,0),(0,1),(0,0),(1,1)`, with nuisance fields varied but never used by the specialist. Specialist is a frozen majority lookup over only `(target_pos,target_neg)` learned from support labels; ties/missing keys => UNKNOWN. Evaluation set: exactly 256 rows generated from a frozen seed, target evidence balanced across four pairs, nuisance fields (form/modal/recovery/intent/envelope/toolbar) shifted independently. General arm is byte-for-byte semantic equivalent of #4215 `predicate_forward`, evaluating all six predicate pairs. Graph terminal is recomputed with the general backend outputs except that TARGET_CORRECT is replaced by specialist output. Timing endpoint uses 20,000 repeated warm calls per arm after 2,000 warmups on the same fixed evaluation feature rows; report median per-call ns across 9 batches, not single-call minima.

## D
`PASS_TINY_PREDICATE_SPECIALIST_SCOPED` only if: 256/256 target labels correct; UNKNOWN recall=1.0; false executable label on UNKNOWN=0; graph terminal equality=256/256; specialist/general median warm evaluation <=0.50; serialized specialist artifact <=1024 bytes; audit errors=[]; >=10 coherent corruption controls reject; formal1/reruns0/replacements0/tuning0. Any target/UNKNOWN/graph error => FAIL. Semantic gates pass but timing ratio >0.50 => HOLD_GENERAL_BACKEND_ALREADY_CHEAP. Provenance/count/audit ambiguity => STOP/HOLD.

## C
The parent backend is authored linear logic, not Laya/Kev. The timing advantage can arise simply because the specialist evaluates one predicate rather than six. A deterministic rule may be simpler than the learned lookup. Python microbenchmarks do not predict production model latency.

## U
No GUI/input/model/provider/network, no natural semantic distribution, no Astra labeling cost, no live promotion, no claim that all predicates should be specialized.
