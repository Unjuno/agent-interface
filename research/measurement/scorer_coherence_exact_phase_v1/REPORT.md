# Exact scorer coherence phase geometry v1

Issue: #1461. Predecessor #944 / PR #945 remains `HOLD_GRID_TOO_COARSE`.

## Disposition

`PASS_EXACT_COHERENCE_PHASE_GEOMETRY_SCOPED`

Exactly one deterministic formal invocation; reruns/replacements/tuning = 0. Independent audit passes and copied-result corruption controls reject 4/4 changes. Frozen scientific-source hashes are unchanged after formal execution.

## What changed from #944

Only the formal measurement method. #944 used a separately frozen 1 us diagnostic phase grid in addition to exact interval reasoning; its two-attempt boundary+1 ns control had a real 1 ns failure set that the coarse grid could not sample, forcing the canonical HOLD. This successor removes coarse sampling from the correctness gate and uses exact integer circular phase intervals plus an independently implemented closed-form checker. No threshold or live runtime behavior is changed.

## Frozen model

- period: `28571429` ns (35 Hz rounded scheduler period)
- immediate equal-span attempts: n = 2, 3, 4
- integer starting phases: 0..T-1
- an attempt fails when its inclusive span reaches/crosses the next tic transition
- formal cases: boundary-1, boundary, boundary+1 ns, boundary+1 us, T; plus n=3 at 20 ms and 25 ms

## Main exact results

| attempts | exact guaranteed boundary (ns) | failure phases at boundary+1 ns |
|---:|---:|---:|
| 2 | 14,285,714 | 1 |
| 3 | 19,047,619 | 2 |
| 4 | 21,428,571 | 1 |

- n=3, d=20 ms: 2,857,142 failing phases; fraction 0.099999968500.
- n=3, d=25 ms: 17,857,142 failing phases; fraction 0.624999960625.

The predecessor-critical n=2 control at 14,285,715 ns has exactly one failing integer phase: `[28,571,428, 28,571,428]`.

## Construction and audit

- small-domain exhaustive combinations: 33,020
- brute-force / exact interval / closed-form mismatches: 0
- invalid controls rejected: 4/4
- frozen formal rows: 17/17 interval vs closed-form agreement
- independent audit: PASS
- corruption controls: 4/4 rejected
- postformal frozen-source mismatches: 0

## Scope

This is an ideal periodic/equal-span integer-nanosecond geometry result. It does not establish live ViZDoom API latency, scheduler behavior, unequal attempt spans, model latency, gameplay/task effect, X11 performance, token savings, human tempo, or production retry reliability. It is suitable as a diagnostic measurement contract for interpreting live per-attempt spans, not as a live guarantee.

## Integrity hashes

- RESULT.json: `6dcf2944c974cfa806d1b1487642af089a77452f5519bfe84a106e28706890dc`
- AUDIT.json: `4166691c4183241d61102f8352bc8f65f41e1763b2af425acff9b31070cef1f4`
- CORRUPTION.json: `a7a752679d5f8b0cf2b719d4ce63792c3e4aa55b304930408ac1badb1b7f8455`
- FORMAL_INVOCATION.json: `fd12bdad9ce49b6844eeb0f1fc48365c25d5b471c7775f0adc5382115c63ff76`
