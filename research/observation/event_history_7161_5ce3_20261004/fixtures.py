"""Literal synthetic trajectories and expected states, not a GUI producer."""
def e(seq, kind, source='object-A', value=0):
    return dict(seq=seq,kind=kind,source=source,value=value)
CASES = [
 ('not_run', [], 'NOT_RUN'),
 ('prediction_only', [e(0,'PREDICT')], 'NOT_RUN'),
 ('pending', [e(0,'ACTION'),e(1,'PREDICT')], 'PENDING'),
 ('success', [e(0,'ACTION'),e(1,'INTERMEDIATE'),e(2,'EFFECT')], 'SUCCESS'),
 ('success_then_revert', [e(0,'ACTION'),e(1,'EFFECT'),e(2,'REVERT')], 'SUCCESS_THEN_REVERT'),
 ('failed', [e(0,'ACTION'),e(1,'FAIL')], 'FAILED'),
 ('gap', [e(0,'ACTION'),e(2,'EFFECT')], 'UNKNOWN'),
 ('wrong_source', [e(0,'ACTION'),e(1,'EFFECT','object-B')], 'UNKNOWN'),
 ('effect_without_action', [e(0,'EFFECT')], 'UNKNOWN'),
 ('duplicate_sequence', [e(0,'ACTION'),e(0,'EFFECT')], 'UNKNOWN'),
 ('missing_tail', [e(0,'ACTION'),e(1,'EFFECT')], 'UNKNOWN'),
]
COUNTS={name:len(events) for name,events,_ in CASES}
COUNTS['missing_tail']=3
