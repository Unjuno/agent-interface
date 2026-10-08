# Existing compiled runtime cross-domain compatibility v1

Status: **PASS for container-level language/runtime compatibility; live MAP01 and desktop transfer remain separate gates.**

## Question

Can the repository's already-retained `compiled_gui_interface_v1.py` state-graph runtime express both a continuous-control loop and a normal desktop two-step workflow without changing the runtime or introducing a second game-specific executor?

This matters because the product goal is not a DOOM bot. DOOM should stress the same bounded local-control semantics that ordinary computer work uses.

## Exact runtime under test

The test reconstructs and checks the existing repository runtime by Git blob SHA-1 before importing it:

`0c02db714127c8e0f770f9d4ac03699749899d2b`

The independently reconstructed container copy is 17,726 bytes, SHA-256:

`93e47e1ab5ae3450bb4acf9ec9d21c9abc44ca93ffaee25683b22039d9a722ca`

and recomputes to the same Git blob SHA-1. No runtime line is patched for this compatibility test.

The executed compatibility runner is `compiled_runtime_cross_domain_compat_v1.py`, SHA-256:

`f3fe7d18550d641df8c32a44dec993cf5846ed442244fb9b05570711095ccd84`

Its published Git blob `0e3a171f204cdeb181744317ab53beff4d5aff53` matches the Git blob independently computed from the executed bytes.

## Continuous-control encoding

The existing v1 language is used unchanged. The whole control surface is represented as a scoped `target_reference`; it grants no input authority. Fresh admission remains per action.

Predicates are only:

- `surface_present`;
- `zone` = `LEFT`, `RIGHT`, or `GOAL`.

The state graph repeatedly selects a bounded left/right operation from the current observation until `GOAL`, or yields if the surface disappears. Each accepted action has a fresh sequence-bound admission, a terminal release receipt and a later observation/effect check.

This is deliberately a small abstract continuous-control model, not ViZDoom and not a gameplay score.

## Desktop encoding

The same unchanged runtime expresses a two-step desktop method:

- `RED` -> enter token;
- fresh `BLUE` -> confirm;
- fresh `GREEN` -> complete.

A changed-state case switches to `YELLOW` after the first action. The frozen expected-effect check then yields `effect_failed` before the second action. Independent simulated task score remains zero.

## Container execution

Command shape:

```text
python -m py_compile compiled_gui_interface_v1.py compiled_runtime_cross_domain_compat_v1.py
python compiled_runtime_cross_domain_compat_v1.py \
  --runtime compiled_gui_interface_v1.py \
  --episodes 2000 \
  --out compiled-runtime-cross-domain-compat-v1.json
```

The four cases were each executed 2,000 times using deterministic seed `20260915`.

| Case | Passed |
|---|---:|
| continuous positive | 2000 / 2000 |
| continuous target/surface disappears | 2000 / 2000 safe yield |
| desktop positive | 2000 / 2000 |
| desktop changed after first action | 2000 / 2000 safe yield |

Across all 8,000 episodes:

- frontier-model resumptions inside the runtime: **0**;
- failed release receipts: **0**;
- retained test failures: **0**.

Machine-readable result: `results/compiled-runtime-cross-domain-compat-v1.json`.

## Negative live-adapter attempt retained in interpretation

A follow-up attempt connected this unchanged runtime directly to the disposable Xvfb tracker/xterm fixtures. The xterm positive path reached two local actions and `TASK_SUCCEEDED` once the normal backend effect-settle delay was respected. The tracker adapter, however, exposed container-specific X window/focus/mapping instability and failed closed before producing a valid cross-domain block. That partial harness attempt is **not** promoted as evidence and no favorable subset is selected.

This does not contradict the earlier independent Xvfb/XTest cross-domain construction, which already showed real input mechanics. It means the next useful work is adapter composition with retained repository backends, not another synthetic executor.

## H / T / D / C / U

### H — falsifiable hypothesis

The existing compiled local-continuation runtime is structurally general enough to encode bounded continuous control and bounded desktop workflows without a game-specific core execution loop.

### T — minimum test

Use the exact retained runtime blob. Validate both interfaces, run positive and changed-state cases in both domains, require multiple local actions on success, fresh post-action observations, verified release receipts, zero internal model resumptions and fail-closed changed-state behavior.

### D — disposition

**PASS for runtime/language compatibility.**

Do not create a second production reactive executor based on the earlier diagnostic `GenericExecutor`. The existing compiled runtime is the stronger convergence point.

### C — competing explanations / failure modes

- The continuous state here is abstract and may omit MAP01 predicates needed for combat/navigation.
- A `whole_surface` target reference may be too coarse for future continuous-control authority and could require a versioned symbol vocabulary rather than semantic overloading.
- Correct local execution does not guarantee that Astra/Luna authors good predicates, actions or continuation policy.
- Adapter/backend timing and focus remain material in real GUI/X11 environments.
- The current runtime caps one method at 16 action transitions; longer control must compose bounded methods rather than silently expanding authority.

### U — uncertainty

The main uncertainty has moved from core state-graph mechanics to adapters and authored semantics: observation predicates, surface/control binding, backend input terminals, task-relative effect conditions and planner-authored contract quality.

## Architecture decision

For the next product generation, prefer one path:

`planner -> compiled bounded method -> fresh local predicates -> per-action admission -> bounded universal input -> effect verification -> independent task score`

Use this for both desktop and real-time domains. A DOOM-specific fast loop should exist only as an adapter/backend specialization, not as a second authority model.

## Next two transfer gates

1. **MAP01:** map existing typed health/ammo/threat/progress signals plus visual state into the compiled method adapter, while preserving the current input-owner, release telemetry and scorer isolation. Do not tune the method to a particular map path; success remains a separately labelled full-map attempt.
2. **Desktop:** run one existing golden Chromium/Calc task through the same compiled method boundary, preserving target handles/adaptive repair and the independent scorer. Require a changed-state safe stop as well as a successful multi-transition task.

A mechanism should move toward the product runtime only if both transfers survive. This is the route to improving one-stage DOOM capability without sacrificing ordinary computer generality.

## Claim boundary

This test does not establish MAP01 clear, general desktop reliability, frontier-model efficacy, human-level reaction time, cross-platform equivalence or production readiness.
