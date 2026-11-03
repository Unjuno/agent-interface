# T1 A05 result — answer sensitivity with transition-audit hold

The frozen candidate completed all 390 model calls. The frozen raw-only auditor returned `PASS_METHOD`, 390 rows, and no raw/prompt/model identity errors. The 2048-token consolidation cap resolved the A04 truncation: every one of the nine six-episode consolidations ended with `done_reason=stop` at 312 completion tokens.

A separate post-hoc review of the preserved raw output independently reproduced the exact-answer endpoint and added the transition checks requested in Issue #8406. Exact-answer accuracy by schedule was:

| Schedule | Seed 4501 | Seed 4502 | Seed 4503 |
|---|---:|---:|---:|
| Episodic-only | 0.267 | 0.267 | 0.267 |
| Per-episode | 0.433 | 0.433 | 0.400 |
| Batch-2 | 0.567 | 0.567 | 0.567 |
| Terminal | 0.633 | 0.633 | 0.633 |

Five preregistered schedule contrasts exceeded the 0.10 margin in the same direction across all three seeds. This supports `PASS_CADENCE_SENSITIVITY_SCOPED` for exact answers on this fixture/model/configuration only. Terminal had the highest answer accuracy; it is not a policy recommendation.

The transition review found no cumulative-episode coverage or source-ID provenance errors, and the rare exception was preserved in all 21 states where it should appear. However, every one of 12 states containing both contradictory observations omitted the required explicit `kind=conflict`, `value=UNKNOWN` claim. All nine states containing the history pair also failed to retain the complete `draft->published` delta value. The frozen auditor did not check these transition requirements, so its method pass is narrower than the Issue's full audit contract. The overall claim is therefore **`HOLD_NO_CLEAN_TRANSITION_AUDIT`**; do not treat the answer-level result as a complete validation of the idea.

The raw-only formal audit and the post-hoc transition review are separate artifacts. The latter is diagnostic and does not alter or replace the frozen candidate, formal auditor, or raw output. A successor should freeze explicit transition assertions before generation and use a schema/prompt that represents conflict and history deltas directly.

Raw: 390 rows, 1,801,131 bytes, SHA-256 `90d45c9383c517dd7f61c7e4912a0954dcc6633107db9da8e503f49bd545ff67`. Formal audit SHA-256 `094a2b5655ab4da2d0bbcdbfa432bc64d0113cdab53502072ed3a58fc2560af2`. See `SUPPLEMENTAL_REVIEW.json` and `RUN_RECORD.json` for further evidence and complete cost metrics.
