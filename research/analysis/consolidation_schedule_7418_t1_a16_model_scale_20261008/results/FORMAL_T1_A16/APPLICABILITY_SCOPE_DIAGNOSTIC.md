# A16 applicability-scope diagnostic

This posthoc diagnostic reads the frozen ledger, query oracle, and preserved A16 raw JSONL. It invokes no model and does not rerun the registered auditor. The script is `analyze_applicability_scope.py`; its machine-readable output is `APPLICABILITY_SCOPE_DIAGNOSTIC.json`. The raw hash was rechecked against the registered SHA-256 (`5d88e0a1cdfe05a99c5e2e42189fc47be611d7abf237e52fb5e556e3069881dd`).

## Finding

The source ledger records applicability context for `ep01`/`ep02` (`editor/draft/standard`) and `ep03` (`editor/publish/standard`). The frozen consolidation mapping explicitly says to ignore fields outside the mapping and writes only effect value and source IDs for both `common_success` and `rare_exception`. The independent transition auditor checks those mapped fields, claim coverage, and source IDs; it does not require app/mode/surface scope in claims. Therefore A16's `PASS_METHOD` establishes faithfulness to its frozen value/source mapping, not preservation of applicability context.

The `q_common_save` oracle asks for the `editor/draft/standard` effect. It uses the contextual ledger to define the answer, while consolidated arms receive only context-free claims. At prefixes 3–6 (after the publish-mode exception is in the source prefix), the raw responses were:

| Arm | SUPPORTED | CONFLICT | UNKNOWN | Correct exact answers |
|---|---:|---:|---:|---:|
| Episodic-only | 12/12 | 0/12 | 0/12 | 12/12 |
| Per-episode | 0/12 | 12/12 | 0/12 | 0/12 |
| Batch-2 | 3/12 | 9/12 | 0/12 | 3/12 |
| Terminal | 0/12 | 3/12 | 9/12 | 0/12 |

Across all six prefixes, the existing exact-answer totals remain episodic-only 15/18, per-episode 3/18, batch-2 9/18, and terminal 3/18. The per-episode and batch-2 `CONFLICT` outputs cite the common-save and publish-exception sources as conflicting even though their ledger contexts differ. This pattern is consistent with lost applicability scope. At prefix 1, per-episode also answers `SUPPORTED` from a single common episode where the oracle requires `UNKNOWN`; terminal's pre-update UNKNOWN answers at prefixes 3–5 reflect schedule visibility delay. Thus the observed schedule contrast combines cadence, context-free representation, and exposure timing.

## Interpretation boundary

This finding does not alter A16's registered `PASS_METHOD` or its scoped exact-answer contrast on the frozen fixture. It narrows what those results establish: the transition audit did not test scope-preserving faithfulness, and query correctness depends on a contextual oracle while the consolidated evidence omits that context. The aggregate contrast cannot be attributed to cadence alone or generalized to a context-preserving memory design. No GUI, deployed memory, or action-effect claim follows.

Future comparison should either preserve applicability scope in every claim and have the independent auditor check it, or score queries using only information actually retained in each arm. Query families should also contain multiple independently authored questions, not one question repeated across prefixes and seeds.
