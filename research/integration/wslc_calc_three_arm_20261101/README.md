# Three-arm Calc task comparison

Fresh prospectively specified fixed-order WSLc block: eo01 direct guarded execution, eo02 compiled continuation, eo03 fresh model regrounding. All use the same 472/615 blank Calc task, gpt-6.1-sol requested low, one persistent model session per arm, private Xvfb, 1 CPU / 1 GiB and network-disabled containers; host model access is separate. Each route had a route-specific pass condition fixed before launch, one attempt, and no success retry. A common exception-path change attempts to retain cleanup/readback and saved bytes on failure; missing evidence remains unknown. Main at freeze was 6e3b459feafa0d67534abe4de8b207f4dde0eb7d; this snapshot's relevant runtime and named model-client files were previously checked against be0cae0a635e5852924a12c8ae971044cc0ce276, and only evidence changed in between.

| order | route | task interval | launcher interval | calls | input (cached subset) | output | saved effect |
|---|---|---:|---:|---:|---:|---:|---|
| eo01 | direct | 6.445 s | 11.438 s | 1 | 12,185 (0) | 62 | exact 472/615 |
| eo02 | compiled | 5.894 s | 8.281 s | 1 | 12,185 (0) | 78 | exact 472/615 |
| eo03 | fresh | 8.566 s | 10.968 s | 2 | 25,735 (12,160) | 124 | exact 472/615 |

All three passed the specified saved-cell, verified release and final X neutral checks. Direct uses the initial grounding followed by current binding, expected-value OCR and guarded Ctrl+S. Compiled yields SAFE_YIELD / effect_unavailable then uses fresh OCR and guarded Save without replaying entry; its initial pixel reference deliberately represents older values. Fresh asks for a second grounding before its guarded Save. All use scripted entry and Save with known expected-value OCR, not an autonomous general spreadsheet agent.

Extract raw.zip beside audit.py and run python audit.py without optimization. The auditor checks frozen input hashes, route/order/criteria, distinct owner sessions and call IDs, request/image/response associations, saved FODS cells, action and owner releases, final X state and route-specific compiled recovery. Raw candidates, captures, model usage, receipts and saved FODS are retained; private model protocol journals are not included. The WSLc warning states that the memory limit excludes swap.

This is one fixed-order block with one sample per route, a fixed layout and values, different cache conditions and unequal model calls. Task interval excludes startup, fixture preparation and audit; launcher interval includes launched process startup but excludes preparation and audit. Cached input is included in input tokens. It provides a simple direct baseline, not a population speedup, cost estimate, reliability rate, persistent-obstruction or partial-input recovery, third-party-edit resolution, MAP01 completion or project completion. The earlier en01 failure and en02 exploratory success are separately retained in the direct-baseline archive and not silently counted as this block.
