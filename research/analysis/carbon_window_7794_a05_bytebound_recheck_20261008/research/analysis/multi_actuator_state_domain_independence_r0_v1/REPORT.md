# #1849 State-domain independence for multi-instance actuators

Decision: **PASS_MULTI_ACTUATOR_STATE_DOMAIN_INDEPENDENCE_SCOPED**

Formal analytical invocation: **1**. Reruns/replacements/tuning: **0/0/0**.

## Result

Frozen abstract model:
- same-modality actuator instances: 4;
- exclusive state domains: 3;
- actuator→domain bindings: **81**;
- distinct actuator pairs per binding: 6;
- total pair cases: **486**.

Exact classification:
- same-domain alias cases: **162**;
- different-domain cases: **324**;
- domain-aware candidate vs independent resource oracle mismatches: **0**;
- device-ID-only comparator false-parallel cases: **162**;
- missing alias conflict witnesses: **0**.

Every same-domain pair has an explicit generic conflict witness: one operation writes shared exclusive state value 0 while the other writes value 1. Therefore distinct actuator handles alone cannot justify generic concurrent admission.

## Theorem

Under the frozen resource model, two already-authorized same-modality operations on otherwise disjoint surfaces are generically parallel-eligible only when their declared exclusive actuator state domains are non-aliased.

This means capability metadata for multi-seat/multi-instance control must expose the **resource/state-domain partition**, not merely a count of device handles.

A second control shows why declaration completeness remains required: even with different state-domain IDs, an undeclared shared exclusive global resource G creates a false-parallel classification.

## Construction

Before formal, an excluded 9-binding /54-case construction passed:
- candidate/oracle mismatch0;
- alias conflict witness missing0;
- hidden-global false-parallel discriminator=true.

Source was published, remotely read back, synchronized to exact Git blobs, and frozen before the only full formal invocation.

## Integrity

- PLAN/prove/audit source frozen before formal;
- postformal Git blob identities unchanged;
- independent audit: PASS/all checks true;
- corruption controls4/4;
- RESULT SHA-256: `cf03b8cbf523c6c8bebf590028f6b16d20ae9c2a2ff7723451bd1dba356ebb60`;
- AUDIT SHA-256: `c13ec1ee3998c58384ee3a6c1d1c87a0814bb9f04703d0dc3b40de9383b04dd2`.

Exact outputs are retained as deterministic gzip+base64 with hashes in `EVIDENCE_MANIFEST.json`; `RECONSTRUCT.py` restores them.

## Interpretation

This result refines #1643 for #1665: multiple logical/device identities become useful for real actuator parallelism only when the backend exposes genuinely separate exclusive state resources, or a stronger operation-specific commutativity proof exists.

It does not prove any real Linux/X11/Wayland multi-seat backend supplies such independence. Focus, grabs, event queues, compositor state, kernel devices, application-global state and hidden ordering can reintroduce conflicts.

## Scope limits

No real multi-seat, throughput, latency, driver, GUI, model or product claim. A live successor must measure a backend with multiple same-modality actuator instances and independently verify state-domain nonaliasing plus cross-instance effects.
