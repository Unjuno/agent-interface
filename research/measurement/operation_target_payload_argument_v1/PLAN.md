# #1206 payload-argument completeness

TASK: OPERATION-TARGET-PAYLOAD-ARGUMENT-COMPLETENESS-20260918-001

## H
With #1177 target_admissibility fixed, adding only the actual caller-owned opaque payload_ref value closes the remaining #1178 synthetic representation gap and permits a deterministic safe rule to return one acceptable disposition for all 96 #1133 rows.

## T
Regenerate exact #1133 corpus from seed 113320260918001 and require semantic digest ea4a86baf3d2efc6f79f75703ef164d2c830cd3f5634e7ad057c26315da752dd. Add target_admissibility exactly from pre-decision target facts and add payload_ref value only when the authored TYPE_TEXT payload is available. Target/payload literal values are output arguments, not decision branch keys. Run one primary replay after source-first freeze, reruns0.

## D
HOLD_NO_LEARNED_RESIDUAL_AFTER_ARGUMENT_COMPLETION iff exact acceptable membership96/96, positives48/48, negatives48/48, false executable negatives0, incompatible structural signatures0, missing executable arguments0, audit/integrity pass. Otherwise follow Issue #1206 dispositions.

## C
Synthetic corpus may be deliberately easy; deterministic closure does not establish real-data sufficiency.

## U
No model/live/task/token/production claim. Stop after first result.
