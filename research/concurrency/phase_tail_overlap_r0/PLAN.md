# Phase-level overlap under one serialized input resource

Parent: #23. Analytical successor to #1643.

## H
Suppose each independent intent has (1) one non-preemptive input burst of duration p_i on a single exclusive global actuator G, followed by (2) a surface-local effect/verification tail of duration q_i that consumes no G and may overlap other independent work. Then whole-intent serialization is unnecessarily conservative. Among all safe schedules that serialize only G, ordering input bursts by non-increasing q_i minimizes final makespan max_i(C_i+q_i).

## T
Analytic adjacent-exchange proof plus one frozen deterministic exhaustive formal. Enumerate n=2..5, p_i in {1,2}, q_i in {0,1,2,3}; compare longest-tail-first (LTF) to every permutation. Baseline is whole-intent serialization sum_i(p_i+q_i). No GUI/model/network/runtime mutation.

## D
PASS_PHASE_LEVEL_OVERLAP_SCOPED iff all 37,440 job vectors have LTF equal to brute-force optimum, counterexamples=0, and at least one strict improvement over whole-intent serialization exists for every n=2..5. Retain exact maximum observed speedup only as bounded-search evidence.

## C
The theorem fails if a tail actually consumes G, two tails conflict through hidden global state, later input depends on an earlier tail result, or cancellation/authority requires whole-intent exclusivity. Those conditions require conflict/dependency edges and may remove the overlap.

## U
Abstract deterministic scheduling only. Tail durations are assumed known for ordering, input bursts are non-preemptive, tails are independently runnable, and no particular GUI/backend is proven to satisfy those assumptions. A live successor must identify actual resource occupancy/effect-pending intervals and fail closed on hidden conflicts.
