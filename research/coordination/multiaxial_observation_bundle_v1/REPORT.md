# Multiaxial observation source-capability gate v1 — result

Task: `MULTIAXIAL-SOURCE-CAPABILITY-GATE-20260917-001`  
Issue: #760 (Rung-0 child of #753)  
Publication BASE: `6a36ecbdf782d02d280b31f368d5542b9527f591`  
Frozen source HEAD before formal: `2473a710cdb15e77582f843733c78d23c3c8bc4d`

## Decision

**`PASS_MULTIAXIAL_SOURCE_CAPABILITY_GATE_SCOPED`**

One frozen runner invocation produced **48/48** deterministic first rows. Formal reruns/replacements: **0**. The frozen auditor returned no errors.

## Scoped result

- `CAPABILITY_GATED` matched the preregistered included/rejected/omitted/unsupported sets **24/24** candidate rows.
- Zero source-family/context violations were model-visible in the candidate arm.
- `RELEVANCE_ONLY` exposed a disallowed higher-ranked source in all **16/16** frozen discriminator rows (pixel-only hidden engine state, coding secret, renderer debug state, and out-of-scope parallel window).
- Budget omission and unsupported-source handling matched the frozen expectations in every repetition.
- Every included item's source identity, kind, context, timestamp/currentness, evidence role, provenance and payload reference remained exactly equal to the registered source metadata.
- Malformed presentation controls rejected **5/5**, including role override and historical→current override attempts.

This establishes only deterministic source-capability/provenance semantics for heterogeneous observation bundles. It does **not** establish that richer bundles improve a model, reduce planner boundaries, or justify deeper sources for a task whose contract forbids them.

## Integrity

Full formal JSON SHA-256: `ebc8d23640d80516e85f1d6c2e6cabd85d107e9c8b19eade5fc8f85a5d092293`  
Audit JSON SHA-256: `ee4d98baea14f780d7d8df25119f1bb952bbf2eaab00984e0ea88ffa10b4f814`

The exact full formal JSON is retained as deterministic gzip+Base64 text in `formal.json.gz.b64`; `reconstruct_formal.py` decodes it and verifies the frozen SHA-256. The helper is post-measurement publication tooling and is not part of the measured source freeze.

## Next discriminator

Use the **same allowed source capabilities in both arms** on a frozen task that genuinely requires a cross-source relation. Compare:

1. `SERIAL_SAME_SOURCES` — the model retrieves the same authorized evidence sequentially;
2. `COMPILED_BUNDLE` — the same authorized evidence is packaged together under a bounded query.

A useful first domain is software debugging where the relation spans a failing test, relevant source function, and one runtime/log or caller context. The compiler must not gain privileged sources relative to the serial baseline.
