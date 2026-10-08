# Generation fence for deferred proposals after threat-authority handoff

Task `MAP01-THREAT-DEOPT-HANDOFF-FENCE-20260917-001`, Issue #619.

## Decision

**`PASS_AUTHORITY_HANDOFF_GENERATION_FENCE_SCOPED`.**

#609/PR #616 established active resource ownership: navigation deoptimization cannot steal a locomotion resource while a valid threat authority owns it. This successor asks the next single question: what happens to already-ready proposals when that authority ends?

The baseline `authority_guarded` protects only currently active authority. Once the lease expires or becomes invalid it falls back to latest-ready selection, so an old deopt or an authority-bound threat proposal can execute after the boundary.

The candidate `handoff_fenced` adds one mechanism: **resource generation binding across authority handoff**. A proposal must match the current resource generation. An authority-bound proposal additionally requires that authority to still be active. Handoff/context invalidation advances the resource generation; prior-generation proposals therefore stay refused until refreshed/reissued.

## Formal block

Source-first GitHub freeze/readback completed before measurement. Construction `py_compile` PASS and 8/8 unit tests PASS. Formal runner was invoked exactly once. Eight scenarios × four repetitions × two policies = **64 first rows / 32 candidate outcomes**. No rerun, replacement, extension or threshold tuning.

| Scenario | baseline | handoff-fenced | n/policy |
|---|---|---|---:|
| expired old deopt | deopt executes | refuse | 4 |
| expired fresh deopt | deopt | deopt | 4 |
| expired old threat | threat executes | refuse | 4 |
| expired current-gen but unowned threat | threat executes | refuse | 4 |
| invalidated old deopt | deopt executes | refuse | 4 |
| no authority, current deopt | deopt | deopt | 4 |
| threat-fire + deopt-locomotion | both | both | 4 |
| active overlapping threat + deopt | threat | threat | 4 |

Frozen independent audit: PASS, errors 0.

- candidate correct **32/32**;
- baseline stale/unowned post-authority executions **16/16**;
- candidate stale/unowned executions **0/16**;
- fresh/no-authority deopt liveness **8/8**;
- non-overlap concurrency preserved **4/4**;
- active threat authority preserved **4/4**.

Four copied-evidence corruption controls were rejected 4/4.

## Interpretation

`defer` is not the same as `fresh later`. Authority termination is a freshness boundary. A proposal authored under the previous resource generation must not silently become authorized merely because the owner disappeared. This applies symmetrically to deferred navigation repair and to stale threat proposals.

The fence is intentionally conservative. A semantically still-valid old proposal must be explicitly revalidated/reissued into the new generation. The fixture does not discover semantic equivalence automatically.

## H / T / D / C / U

**H:** post-authority proposals require a resource-generation handoff fence in addition to active ownership arbitration.

**T:** deterministic stdlib fixture, eight scenarios × four repetitions, exactly one formal invocation, frozen independent audit.

**D:** PASS at the frozen gate above.

**C:** generation changes are authored by the fixture. A real scheduler still needs an authoritative trigger for generation advance and an explicit revalidation path.

**U:** no ViZDoom timing, physical input, model, natural handoff rate, fairness, rollback or multi-owner resource graph is measured.

## Next single question

Do not add another scheduler rule in a synthetic fixture. Transfer `resource authority + generation handoff` together into the smallest real normal-MAP01 overlap diagnostic, holding the retained threat policy and no-progress deoptimization mechanisms fixed. The transfer should measure actual proposal age/generation, authority start/end, selected motor resource and release state.
