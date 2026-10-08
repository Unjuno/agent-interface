# T1-A15 typed conflict eligibility

A15 is a fresh exploratory continuation of the #8406 model-facing consolidation-schedule evaluation. It tests whether typed positive and negative examples improve transition faithfulness after A14 produced false conflicts between verified patterns, a premature fact conflict, a mismatched conflict record, and a distorted exception effect.

Only the consolidation prompt’s conflict section changes from A14: it adds an explicit eligibility filter and four symbolic cases distinguishing ineligible claim kinds, singleton facts, agreeing fact observations, and genuinely conflicting fact observations. The fixture, JSON Schema, four schedule arms, checkpoints, queries, model digest, decoding, and independent auditor remain fixed. Fresh seeds are 5501, 5502, and 5503. No earlier run output is pooled.

The 390-call allocation and interpretation gates are in `PROTOCOL.md`. Frozen inputs and results are under this package; raw candidate rows, preflight, and independent audit belong in `results/FORMAL_T1_A15/`.
