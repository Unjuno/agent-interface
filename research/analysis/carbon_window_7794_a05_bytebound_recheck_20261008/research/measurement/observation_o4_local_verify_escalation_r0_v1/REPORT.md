# O4 local VERIFY escalation contract — retained R0 result

Issue #1650.

## Disposition

**PASS_O4_LOCAL_VERIFY_ESCALATION_CONTRACT_SCOPED**

The scoped contract allows local suppression of a model escalation only when a verifier receipt is bound to the current observation and current intent, explicitly non-authoritative, and resolves to TRUE or FALSE. UNKNOWN, stale observation, intent mismatch, missing receipt, and authority-forged evidence all escalate.

## Formal result

One exact frozen formal invocation, reruns0/replacements0/tuning0.

- rows: 250,000
- candidate/oracle mismatch: **0**
- current TRUE/FALSE local resolutions: **71,822**
- escalations: **178,178**
- naive lineage-blind unsafe suppression discriminator: **107,361**
- directed cases: **7/7**
- audit: PASS, errors []
- corruption controls: **5/5**

The naive comparator is intentionally not a candidate. It demonstrates that a TRUE/FALSE verifier result without observation/intent/currentness/authority binding is not a safe escalation-suppression rule.

## Integrity incident retained

After source publication, one local execution was discovered to use scientifically equivalent but byte-nonidentical source because comments from the construction file remained. It was rejected before formal classification and is not used as evidence. The exact remote frozen source was reconstructed and verified with `git hash-object` against GitHub blob IDs before formal1. No threshold, seed, corpus, mechanism, or decision rule changed.

## Scope

This is a synthetic state-machine contract. It does **not** show that a real GUI local verifier is accurate, faster than a model, or beneficial end-to-end. Verification evidence grants no input or semantic authority. The next useful rung is a retained-evidence or real-app O4 transfer using an independently scored deterministic predicate and an UNKNOWN/stale control.

Broad ROADMAP O4 remains open until such transfer evidence exists.
