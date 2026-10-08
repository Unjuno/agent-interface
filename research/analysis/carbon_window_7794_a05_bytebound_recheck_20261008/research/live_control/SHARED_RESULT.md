# Self-contained duplicate result experiment

shared_result_v1 stores repeated dict/list JSON values of at least 256 canonical bytes once in a definitions map. A document and explicit reference-path list refer to those complete literals. Only listed paths are decoded as references, so original data shaped like a reference marker remains literal. Unknown fields and negative evidence are preserved, not summarized or classified away. The original source hash is retained. Duplicate input JSON keys and non-finite values are rejected.

## Results

Nine archived Calc/browser result payloads round-trip to exactly equal JSON values, including every receipt attention entry and task-success field. Six controls cover repeated negative evidence, literal reference-like data, boolean/integer/float distinctions, empty/scalar values and array nesting. Two invalid-source cases and three corrupt-encoding cases are rejected. This is JSON-value equality, not preservation of whitespace/key order or proof of readability.

Full encoded size includes definitions, references, document, format, source hash and scope. Seven completed results shrink by 267–743 canonical bytes; two pending early results grow by 41/42 bytes. Across all nine, 86107 canonical bytes become 81696, a 5.12% reduction. Empty input grows from 2 to 302 bytes. Repeated negative data itself grows slightly. The threshold does not guarantee a net win because representation overhead matters.

All original data is retained in the new payload, with no external fetch required to reconstruct it. However a model has to resolve references, and lifecycle observation fields not structurally identical to their state-table representation are not removed by exact object sharing. This explains why apparent visual duplication produces limited measured savings here.

## Decision

Do not adopt this as the default presentation. A roughly five-percent byte reduction on these archives is insufficient evidence for improved model input tokens, cost, decision accuracy or tempo, and pending payloads regress. No token counts or new model-facing usability trial were measured. Keep this candidate and its mixed results; do not tune thresholds repeatedly against the same nine records to manufacture a better headline.

Next prioritize a measured model-facing presentation contract: record what was actually sent, identify unavailable token/model-receipt endpoints explicitly, and compare a task with meaningful negative evidence. A simpler non-duplicated result composition may be easier to use than general references, but it must preserve required diagnostics and demonstrate benefit before promotion. Existing runtime/client defaults remain unchanged.
