# Persistent geometric world state R0 — retained result

Issue #1562, parent idea #1526.

## Disposition

**PASS_PERSISTENT_GEOMETRIC_STATE_PROVENANCE_R0_SCOPED**

One frozen formal invocation, reruns0/replacements0/tuning0.

## What was tested

A typed external geometry store preserves:
- provenance role: OBSERVED / INFERRED / UNKNOWN;
- source epoch;
- entity generation/currentness;
- current observed geometry across removal of conversational/source payloads by `COMPACT_CONTEXT`.

It was compared with an intentionally weaker `LATEST_GEOMETRY_ONLY` baseline and an independently structured event-history oracle.

## Formal result

200,000 deterministic traces, seed `152620260918001`, 16 entities.

- candidate/oracle mismatches: **0**
- candidate false-current promotions: **0**
- candidate fresh-current overinvalidations: **0**
- compaction semantic changes: **0**
- fresh re-observations accepted current: **40,000**
- ABA stress: **40,000**
- compaction stress: **80,000**
- occlusion stress: **40,000**
- inference stress: **80,000**
- baseline false-current promotions: **120,000**

The independent audit regenerated the same corpus metrics and disposition. Corruption controls for false-current, oracle mismatch, overinvalidation, compaction mutation and missing baseline discriminator all triggered rejection as intended.

## Interpretation

This establishes only a scoped representation/currentness prerequisite: if persistent geometric state is later used by Agent Interface, provenance role and non-rebindable currentness identity prevent historical/inferred geometry from silently becoming current evidence after context compaction, generation changes, occlusion and ABA-like returns.

It does **not** establish that persistent geometric state improves Astra reasoning, task correctness, model tokens, latency, memory compression, object association, 3D reconstruction, or general GUI control. The baseline is deliberately weak, so this PASS is a semantic safety discriminator, not a product comparison.

## Next legal rung

Do not promote this schema directly to runtime. A successor should bind the same semantics to already-retained real observation/target receipts from at least two domains, or run a matched model-facing comparison in which the persistent store changes only the supplied world-state representation. Historical/inferred geometry must remain non-authoritative.
