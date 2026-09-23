# Multi-cursor parking / reposition R0 — result

Decision: **PASS_MULTICURSOR_PARKING_REPOSITION_SCOPED**

Parent #1643. This result isolates one serialized physical pointer and asks whether remembered logical cursor parking positions reduce physical reposition work without introducing a separate relocation primitive.

## Proof result

For target sequence x0..xn, after each serialized action the physical pointer endpoint is the preceding target. Under the alias rule, activating any parked logical cursor for the next target still materializes the same physical endpoint transition, so every transition costs |x_i-x_(i-1)| regardless of logical label count. Summing yields identical SINGLE and ALIASED_PARKED physical reposition cost.

A separately declared switch/warp primitive of cost s changes the transition cost to min(m_i,s). Its exact total gain is sum(max(m_i-s,0)), with strict gain iff at least one physical transition cost exceeds s.

## Exhaustive result

Complete target corpus over positions {0,1,2,3}, sequence lengths2..6:

- sequences: **5,456**
- logical cursor counts checked:2,3,4
- SINGLE/ALIASED comparisons: **16,368**
- alias mismatches: **0**
- switch costs s=0,1,2,3
- switch/formula comparisons: **21,824**
- switch mismatches: **0**
- strict positive-control gain cases: **12,466**
- formal invocations1 / reruns0
- independent audit PASS/errors[]
- source rehash6/6

Canonical examples:
- stationary [2,2,2,2]: cost0; no possible reposition gain;
- alternating-near [0,1,0,1,0]: SINGLE=ALIASED=4; switch s=1 gives no gain;
- alternating-far [0,3,0,3]: SINGLE=ALIASED=9; switch s=1 costs3, gain6;
- monotone [0,1,2,3]: SINGLE=ALIASED=3; switch s=1 gives no gain.

Hashes:
- RESULT.json `b4da5eaa7f8cb8f56ab1f634b958384eee1abfaedb199c33c14e2210b2d3f769`
- AUDIT.json `24b64307d50694474fddd3cd5896ef6b778f97cb0a8c4d4358818225e0567310`
- SOURCE_REHASH.txt `584a28bc96e32969d645fc03aaace06f5bb71f7c6a5486cd374892314932a665`

## Interpretation

Visible/logical cursor multiplicity by itself does **not** reduce physical reposition cost under a serialized endpoint-cost pointer model. If a backend makes relocation cheap through absolute warp, direct target activation or another switch primitive, that primitive is the cause of the gain and should be benchmarked independently of cursor count.

This does not reject independent multi-pointer resources from #1643, and it does not establish live X11/Wayland latency, hover/path equivalence, semantic target-currentness savings, application correctness or human tempo.

The next discriminating live successor should measure one variable only: actual backend relocation cost versus ordinary physical movement, or semantic target re-grounding savings with freshness guards.
