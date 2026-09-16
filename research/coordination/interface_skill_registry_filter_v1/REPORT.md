# Interface skill registry applicability filter v1 — result

Task: `SKILL-REGISTRY-APPLICABILITY-FILTER-20260917-001`  
Issue: #757 (Rung-0 child of #751)  
Publication BASE: `ac114c6648ad47673214e341df8edbba592d1c5e`  
Frozen source HEAD before formal: `3cb75f3a9928b2532ce061bbf7fe4e41bd7bb75e`

## Decision

**`PASS_SKILL_APPLICABILITY_FILTER_SCOPED`**

One frozen runner invocation produced **64/64** deterministic first rows. Formal reruns/replacements: **0**. The frozen auditor returned no errors.

## Scoped result

- Applicability-aware policy selected the preregistered valid/revalidation/fallback path **32/32** candidate rows.
- Hard-invalid top semantic candidates were rejected before implementation-detail loading in every applicable candidate case.
- The semantic-only negative control exposed a hard-invalid or revalidation-required top candidate **32/32** rows.
- Historical `HINT` remained a `HINT`; in the one permitted case it became usable only through a distinct current `ADMISSION_DEPENDENCY` revalidation receipt. No in-place evidence-role promotion occurred.
- Skill version/provenance/implementation identity remained exact.
- Malformed registry controls (missing version, missing provenance, unknown role, forbidden in-place HINT promotion) rejected **4/4**.

This establishes only deterministic registry/filter semantics. It does **not** establish embedding quality, model-facing retrieval benefit, token reduction, automatic skill generation/consolidation, or real GUI execution correctness.

## Integrity

Full formal JSON SHA-256: `aae9e695776c782d7c4fc3e7fe4fe4a83ebb5b7813d75a9c9b22ba0171d2eb8c`  
Audit JSON SHA-256: `d644fdeeac0d9113dbe2f7e0a12d6e507a637e901c80afdce737ff49ece92dda`

The exact full formal JSON is retained as deterministic gzip+Base64 text in `formal.json.gz.b64`; `reconstruct_formal.py` decodes it and verifies the frozen SHA-256. The helper is post-measurement publication tooling and is not part of the measured source freeze.

## Next discriminator

The next high-information rung is model-facing retrieval with the same underlying skill set:

1. `FLAT_CATALOG`;
2. `SEMANTIC_ONLY`;
3. applicability-aware compact candidate cards + lazy detail.

Hold execution semantics and ordinary authority admission fixed; measure correct skill/abstention, out-of-envelope selection, detail expansions, actual model-visible tokens/schema size, fallback, and final task correctness.
