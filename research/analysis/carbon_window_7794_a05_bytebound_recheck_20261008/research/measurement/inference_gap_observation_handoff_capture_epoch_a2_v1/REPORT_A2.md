# #1506 capture-epoch handoff A2 formal result

Decision: **PASS_CAPTURE_EPOCH_CURRENTNESS_ACROSS_HANDOFF_SCOPED**.

#1493 remains a no-result monolithic execution stop. A2 changes only execution/serialization granularity to 40 immutable batches x 5,000 histories. The exact inherited model/oracle/trace generator/engine bytes, seed, global order, family counts and decision gates are unchanged.

## Formal outcome

- histories: 200,000
- candidate/oracle mismatches: 0
- delayed old-epoch stress: 60,000
- candidate old-epoch CURRENT labels: 0
- multi-handoff old-epoch CURRENT labels: 0
- delivery-bound comparator false-current old labels: 60,000
- fresh current opportunities/current labels: 180,000/180,000
- fresh identities preserved after later old delivery: 60,000
- cross-scope invalid: 15,000
- forged/future invalid: 15,000
- malformed invalid: 10,000
- duplicate current: 20,000
- fresh current after multiple handoffs: 20,000

All 40 formal batches have exactly one START and one RESULT; reruns/replacements/tuning are 0. All 40 independently regenerated batch audits pass with exact history digests. Aggregate audit passes; copied-result corruption controls reject 5/5 mutations. Postformal inherited/source harness SHA-256 values match the frozen source.

Descriptive batch compute only (not a performance endpoint): min 665.160 ms, median 985.928 ms, max 1652.787 ms per 5,000-history batch.

The grouped outer shell invocation returned timeout after batch39 stdout; immediate readback showed all40 START and RESULT files had already serialized. No batch was rerun.

## Interpretation

A delayed pre-handoff observation must not become current merely because it is delivered after handoff. Binding planner-context currentness to immutable capture epoch eliminates the 60,000/60,000 false-current cases exposed by delivery-order currentness while preserving every fresh-current opportunity. This is a synthetic observation-role composition result, not action authority or live GUI evidence.

## Scope

No model, X11, GUI, network, task input, token, MAP01, human-tempo or production-runtime claim. A production ABI may represent the same semantic requirement with generation/request-origin/sequence identity rather than a literal `capture_epoch` field.
