# #1550 retained temporal-sheet identifiability audit

TASK: `TEMPORAL-SHEET-RETAINED-IDENTIFIABILITY-20260918-001`
BASE: `18dd04cb494d702aa41c33b23de9146bbf84b6c6`
Parent: #1525; scientific parent: #746.

H: retained model-facing evidence does not identify a causal benefit from packing temporal history into one spatial sheet because no fully matched presentation-only comparison exists.

T: retained-data/container-only audit. Pin the repeated `temporal_sheet` implementation, inspect at least three model-facing retained families, normalize tempting comparison pairs, and require exact matchedness of model/effort/current+history evidence/prompt-schema/session-cache/task-oracle while presentation alone differs. #752/#808 remain model-free background, not model efficacy evidence. One deterministic invocation; reruns/replacements/tuning0.

D: PASS_NOT_IDENTIFIABLE iff >=3 families are pinned, admissible presentation-only pairs=0, every candidate pair fails at least one gate, model-free parents are scoped correctly, and independent audit/corruption controls pass. PASS_IDENTIFIABLE only for >=1 all-gates pair. HOLD_SOURCE_GAP only if matchedness cannot be classified.

C: identical current/model image does not establish identical prompt/session/oracle; cross-controller runs are confounded; model prose mentioning motion is not causal evidence; current-only vs history answers a different question from packed-vs-separate presentation.

U: no new model/GUI/input call and no claim about temporal-sheet quality, token savings, latency or task success. A future efficacy test must use a fresh matched prediction-only allocation.
