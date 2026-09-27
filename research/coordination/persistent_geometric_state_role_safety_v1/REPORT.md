# Persistent geometric state role-safety — formal result

Task `PERSISTENT-GEOMETRIC-STATE-ROLE-SAFETY-20260918-001`, Issue #1560.

## Decision

**`PASS_PERSISTENT_GEOMETRIC_STATE_ROLE_SAFETY_SCOPED`**, with a retained frozen-auditor v1 defect and passing postformal independent auditor v2.

## First formal outcome

Exactly one frozen formal invocation used seed `156020260918001` over 20,000 randomized state/operation sequences plus 20 directed role/freshness/roundtrip rows. No rerun, replacement or tuning.

- weak-role direct actuator rejections: **3,314**;
- valid current admission executions: **841**;
- historical/expired admission rejections: **2,479**;
- planner projections preserving records: **3,436**;
- explicit revalidation successes: **3,375**;
- entity/surface/expiry revalidation refusals: **3,307**;
- snapshot/restore operations: **28,302**;
- invalid backend emissions: **0**;
- role/currentness escapes: **0**;
- provenance mutations: **0**.

Directed matrix mismatches and invalid backend emissions were both zero. Row digest: `3e3cf3901ec544bdb491581330fd0bcb3d907bae4db5baaef38a6b4d663f36bb`.

## Retained audit defect

The source-frozen auditor v1 failed with `errors=["counts","row_digest"]`. The formal result was **not rerun**. Inspection showed the auditor independently regenerated the fixed-seed schedule but failed to consume the validity-horizon RNG draw used by the frozen formal generator in its admission template, causing later schedule drift. This is an auditor defect, not a candidate/source change.

`AUDIT_FAILED_V1.json` remains retained unchanged. A separate postformal `audit_v2.py` changes only the independent regeneration bookkeeping by consuming that frozen draw. It does not import the candidate implementation and does not change the formal result. Auditor v2 reproduced the exact formal counts and exact row digest `3e3cf3901ec544bdb491581330fd0bcb3d907bae4db5baaef38a6b4d663f36bb` with `errors=[]`. Eight copied-result corruptions were rejected 8/8 by the v2 audit.

## Interpretation

At this scoped boundary, persistence can preserve geometry plus evidence role/freshness/provenance without creating actuator authority. Snapshot/restore and planner projection are not promotion operations. Historical `HINT` remains non-authoritative; the only tested promotion path creates a **new** `ADMISSION_DEPENDENCY(CURRENT)` after explicit `REVALIDATE_CURRENT` consumes fresh same-entity/same-surface current planner context. Old records remain unchanged.

This supports a minimal safety contract for the architectural idea in #1526. It does **not** show that persistent world state improves Astra, survives actual model-context compaction better than conversation state, reduces tokens/latency, improves task success, or that the five-role vocabulary is complete. Geometry can remain stale while provenance is perfectly preserved, so current revalidation remains mandatory before actuation.

## Execution

Formal wall time 2.19 s; max RSS 93,356 KiB; Python 3.13.5. These are descriptive container measurements, not performance gates.
