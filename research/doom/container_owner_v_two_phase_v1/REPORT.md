# Real MAP01 owner-deadline vs two-phase observation mechanism selection v1

Status: **OWNER_PARETO_TIMING_CANDIDATE_REQUIRES_SEMANTIC_REPAIR**.

## Question

For a planned ~50 ms physical-authority window on the retained real ViZDoom/X11 MAP01 fixture, which existing mechanism better separates input release from observation publication?

- `owner_deadline`: unchanged v13 observation/publication path, 2000 ms hold, independent InputOwner lease deadline at clock + 50 ms. Terminal is expected to remain `expired` under the unmodified executor.
- `two_phase`: the separately retained PR #120 candidate, ordinary 50 ms hold; raw capture/typed evidence occur before release and durable publication is deferred after release. Terminal is expected `completed`.

No model calls. Same key (`d`), fixture, scorer and X11/ViZDoom stack. Three fresh matched pairs use seeds 993601–993603 in balanced order. No retry.

## Result

Median timing from input acknowledgement:

| Metric | Owner deadline | Two-phase |
|---|---:|---:|
| verified empty | **48.986 ms** | 50.933 ms |
| first typed evidence | **18.489 ms** | 19.208 ms |
| first full artifact | **66.676 ms** | 97.049 ms |
| terminal | **67.979 ms** | 163.622 ms |

Owner deadline → verified empty median is **0.487 ms**.

Paired owner-minus-two-phase deltas:

| Pair | empty | full artifact | terminal |
|---|---:|---:|---:|
| 1 | -1.451 ms | -26.018 ms | -91.208 ms |
| 2 | -1.948 ms | -24.941 ms | -90.531 ms |
| 3 | -10.001 ms | -41.425 ms | -116.356 ms |

Hard gates all pass: verified release 6/6, strict terminal score agreement 6/6, scorer missed periods 0, controller scorer leaks 0, and owner-verified empty precedes the in-flight first full artifact 3/3. Owner terminals are `expired` 3/3; two-phase terminals are `completed` 3/3.

## Decision

Retain **owner deadline as the timing Pareto candidate**, but do not promote unchanged `expired` semantics as planned completion. Existing project evidence explicitly keeps unexpected expiry distinct from completion. The separately retained `dual_lifetime_executor_v1` / `authority_ended` work supplies the relevant semantic direction: scheduled authority end is a partial lifecycle boundary, not `PROGRAM_COMPLETED` or task success.

Therefore the two-phase publication candidate remains useful evidence for ordinary worker-managed completion, but it should not be layered onto owner-deadline paths merely for physical-release timing. The next smallest integration is model-free caller handling of the already-existing `authority_ended` receipt contract.

## Provenance

- runtime source base: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`
- two-phase candidate source retained in main at `e31ce43995f399555bba40ed6efe9840c7fdf983`
- runner SHA-256: `f4ea0106e965ced73db9981922729ae360b73f1285c133604f24c4552cd61354`
- preregistration SHA-256: `bbeb23f07581c4f4c5be9707dd6928adcf8436e46f9200d972c7cd0575696503`
- result SHA-256: `e9707bb38cf7961ad26de8c3d4fe0223bd90f04bc5764a7e66bd3459691779e9`
- raw evidence ZIP: 6,142,525 bytes, SHA-256 `c0306eb52390fda39f0f731b32d5df3903ce9da36d984d4f687a233a98105ebe`

## Scope

Zero-model real ViZDoom/X11 mechanism-selection evidence only. No gameplay efficacy, population rate, hard-real-time, planner, or production-semantic claim.
