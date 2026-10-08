# Early saved-effect publication before final scoring

Candidate interactive_v23 / finalization_v3 emits a separate `effect_evidence`
after closing input admission and sampling the saved cells, before the unchanged
independent evaluator. The final evaluation still includes the sampled effect.
`effect_output_flushed` is distinct from final `output_flushed`. A failed early
publish is retained in `effect_publication_error`; scoring and final publication
continue. A later successful final publish does not erase the early error.

Two scripted Calc runs repeat v22's seed, tasks, step lists and presentation:

| Case | v22 first effect emission | v23 early effect emission | v23 final evaluation emission |
|---|---:|---:|---:|
| Save | 27.924 ms | 24.144 ms | 37.833 ms |
| Unsaved | 3023.367 ms | 18.585 ms | 3032.829 ms |

Times start at program terminal creation and end at runtime emit entry, not
model receipt/comprehension. Both v23 early records and final records were read by
the subprocess supervisor and have flush receipts. Saved XLSX hashes match the
sampled evidence; save remains VERIFIED with [532,590], unsaved CONTRADICTED with
[null,null]. Program terminals remain completed with verified release.

The known unsaved evaluator wait is no longer on the effect publication path.
This does not establish general end-to-end agent acceleration: one run per case,
sequential cohorts, scripted controller, no model input-token measurements. The
additional event increases output volume. Finalization status remains pending
until final evaluation completes; early evidence is available on the event lane,
not yet through an intermediate retained-status query.

`audit_live_saved_effect_v2.py` verifies runtime source hashes, fourteen exact
public AIT/PNG frames, publication order, identical early/final effect and receipts.
Four callback controls cover UNKNOWN normal output, scorer exception, failure of
both publications and early-only failure. Early-only failure retains computed
score, final output confirmation and a finalization_error at publish_effect.
These are callback failures, not live blocked-pipe tests. Permanently blocked
early publication can still delay scoring; this candidate is synchronous.

Results: `results/live-saved-effect-03` and
`results/live-saved-effect-early-audit.json`. Frozen v22/results remain unchanged.
No default promotion or freeze credit. Next exercise the new event with actual
assistant self-use and test live publication failures before treating it as a
reliable planner boundary. Early cell evidence remains scoped historical state,
not causal attribution, recovery authority, or whole-workbook correctness.
