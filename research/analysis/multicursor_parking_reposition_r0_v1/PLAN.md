# Multi-cursor parking / reposition R0

Task `MULTICURSOR-PARKING-REPOSITION-R0-20260918-001` / Issue #1654.

## H
For one serialized physical pointer with endpoint movement cost `m(x,y)=|x-y|`, logical cursor aliases with remembered parking positions cannot reduce physical reposition cost if activating any alias must still materialize the same physical endpoint transition. A separate switch/warp primitive of cost `s` can reduce cost; its exact gain is `sum(max(m_i-s,0))`.

## T
Enumerate all target sequences of lengths2..6 over positions0..3. Compare SINGLE, ALIASED_PARKED for logical cursor counts2..4, and SWITCH_PRIMITIVE for s=0..3. Retain stationary, alternating-near, alternating-far and monotone examples. Standard library only.

## D
PASS iff SINGLE==ALIASED for every sequence/cursor count, switch direct cost matches the closed form for every sequence/s, at least one strict positive-control gain exists, formal1/reruns0, and independent audit/source integrity pass.

## C
Real pointer warps, independent seats, hover/path semantics, revalidation and semantic grounding are outside this model.

## U
No live OS latency, application correctness, token or human-tempo claim.
