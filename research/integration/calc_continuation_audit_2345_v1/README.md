# Calc continuation integration audit (#57)

## H/T/D

This additive audit reads the retained main summaries for `calc-final-drain-01` and `calc-settle-self-use-01`. It checks same-response final evaluation, cleanup, independent saved-effect evidence, and that pixel quiet remains `semantic_completion=unknown`. Reproduction:

```
python3 research/integration/calc_continuation_audit_2345_v1/run_audit.py
```

The source blobs are pinned in `RESULT.json`. No retained evidence is rewritten and no runtime/model/GUI run is performed.

## C

The two sessions are not a matched baseline or integrated efficiency comparison. Model tokens, human baseline, outer latency, and generality remain unavailable. The audit therefore does not claim a speedup or task-quality improvement.

## U / stop

Disposition: `PASS_EXISTING_CONTINUATION_EVIDENCE_AUDIT_SCOPED` (7/7 checks). The next integrated acceptance workload must charge caller assembly, observation, model and verification costs across cold, warm, invalidation and repair phases.
