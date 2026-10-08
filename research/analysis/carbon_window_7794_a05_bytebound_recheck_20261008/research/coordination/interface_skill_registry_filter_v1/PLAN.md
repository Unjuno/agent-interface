# Interface skill registry applicability filter v1

Task: `SKILL-REGISTRY-APPLICABILITY-FILTER-20260917-001`
Publication base: `ac114c6648ad47673214e341df8edbba592d1c5e`
Issue: #757; parent #751.

Single factor: selection policy only (`SEMANTIC_ONLY` vs `APPLICABILITY_AWARE`). Semantic scores, registry, contexts and expected applicability are frozen fixture inputs. No model calls.

Formal block: 8 cases x 4 repetitions x 2 policies = 64 deterministic rows, one runner invocation. Four malformed static controls. No same-ID rerun, replacement or post-result threshold/source change.

Primary decision: `PASS_SKILL_APPLICABILITY_FILTER_SCOPED` only if all candidate rows select the expected valid/revalidation/fallback path, hard-invalid top candidates are rejected before implementation-detail loading, HINT promotion occurs only through a distinct current revalidation receipt, identity/version/provenance remain exact, semantic-only exposes the intended negative controls, malformed controls reject, and source/result audit passes.
