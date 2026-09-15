# Conditional reuse and failed-idea revisits: literature convergence v1

Reviewed 2026-09-15. This note maps recent primary research to existing Agent
Interface evidence. It does not import reported benchmark gains into this
repository or treat a paper architecture as locally validated.

## Convergent findings

| Primary source | Reported idea | Local implication | Immediate decision |
|---|---|---|---|
| [MementoGUI](https://arxiv.org/abs/2605.18652) | Treat long-horizon context as online memory selection; keep textual summaries and ROI-level visual evidence rather than replaying all screenshots. | Existing target handles, exact patches, compact normal results and raw-detail retrieval fit this separation. The missing measurement is whether selection retains the evidence needed after an unexpected transition. | Retain as a test direction. Do not add a learned memory controller before a fixed selection/retrieval ablation. |
| [Naive Visual Memory is Not Enough / AGMem](https://arxiv.org/abs/2606.14106) | Full-image memory can shift rather than remove failures; action-grounded crops are proposed to reduce grounding errors. | The current exact target patch should be stored with the action/effect/recovery receipt, not appended as an unscoped old screenshot. Reuse must still check current binding and pixels. | Add action/recovery provenance to the next memory comparison. Keep full-frame history as a matched control, not a presumed benefit. |
| [Adaptive VLM Routing](https://arxiv.org/abs/2603.12823) | Route by estimated difficulty and required reliability; warm memory may reduce escalation. | Typed local evidence can serve as an observable route discriminator. A scalar confidence alone is insufficient for input because current target and authority checks remain necessary. | Continue local-first/same-model fallback. Defer multi-model routing so model identity stays fixed in the next causal comparison. |
| [Mirage-1](https://arxiv.org/abs/2506.10387) | Organize reusable GUI behavior into hierarchical skills and update it for online conditions. | Compiled methods should retain explicit dependencies and yield reasons; repair should update only the invalid binding when evidence permits. | Test selective invalidation and repair through the shared caller before adding another skill hierarchy. |
| [OSWorld](https://arxiv.org/abs/2404.07972) | Use configured initial states, real computer interaction and execution-based task evaluators. | Independent task effect and reproducible reset remain separate from action acceptance and model self-assessment. | Preserve independent fixture/oracle scoring in every live reuse test. |

## What the current implementation already covers

Adaptive caller v3 represents one evidence-backed routing policy:

```text
current cached reference
  -> exact reuse check
  -> eligible local repair, zero model calls
  -> typed missing / ambiguous / changed result
  -> one accounted model reacquisition
  -> one later exact observation and call-bound patch receipt
  -> ordinary authority/admission and independent effect check
```

This agrees with the literature at the level of architecture direction, while
remaining stricter about evidence and authority. The papers do not establish
that this repository's handle, patch, repair relation, timing or token behavior
will transfer to a new application.

## Failed ideas become conditional hypotheses

The revisit ledger remains the admission gate for retesting. A new trial must
name the old retained artifact, the observed failure discriminator and exactly
one causally relevant changed condition. It must preserve the old safety lesson
and freeze the first-result rule before execution. A renamed seed, larger budget
or repeated allocation without a changed mechanism is not a revisit.

The next useful condition matrix is:

| Prior failure or open gap | Changed condition worth testing | Discriminator | Required outcome |
|---|---|---|---|
| Cached semantic relation is known only for resize with unchanged target pixels. | Restyle the control while preserving role and task effect. | Exact target patch changes but a bounded action-grounded neighborhood remains uniquely associated. | Local path must abstain or produce a separately versioned relation; no wrong-target input. |
| Local repair cannot find current evidence. | Move the same target outside the old search radius. | `missing` before model call, then current call-bound target after fallback. | Exactly one model fallback, later exact receipt, independent success and complete accounting. |
| Current evidence contains two plausible controls. | Add a visually similar decoy with different effect. | `ambiguous` with zero executable target. | No local input; fallback may select only with fresh current evidence and the decoy must remain untouched. |
| Full screenshot history may distract grounding. | Compare full prior frame, action crop plus receipt, and no memory under one held-out transition set. | Failure class, actual input tokens, images and wrong-target action. | Retain a memory form only if correctness is no worse and model-visible work falls over the frozen horizon. |
| Compiled method repair currently replaces fixture-known dependencies. | Invalidate one of two independent target bindings. | Dependency receipt identifies exactly one invalid binding. | Repair only that binding; unchanged binding revalidates and no full recompilation is charged. |

## Near-term sequence

1. Run the shared caller on one natural local repair and one natural
   missing/ambiguous/changed fallback with independent task and collateral
   scoring.
2. Add action/effect/recovery provenance to retained crops and compare it with
   full-frame and no-memory controls on a frozen transition set.
3. Exercise selective invalidation of one binding in a multi-target method.
4. Transfer the retained mechanism to OpenTTD or Mindustry before describing it
   as a general desktop/game interface capability.

The external results support this sequence as hypotheses. Only local matched
measurements can decide whether a component enters the shared default.
