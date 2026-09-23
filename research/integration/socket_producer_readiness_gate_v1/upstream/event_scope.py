"""Explicit event identity fields; no inferred action attribution."""
FIELDS={'accepted':'id','terminal':'id','observation':'id','cancel_requested':'id',
        'effect_evidence':'final_program','independent_evaluation':'final_program'}


def validate_scope(action_id,events):
    if action_id is None:return
    if not isinstance(action_id,str) or not 1<=len(action_id)<=128:raise ValueError('bounded action_id required')
    if any(e not in FIELDS and e!='rejected' for e in events):raise ValueError('unsupported scoped boundary event')


def boundary(record,events,action_id):
    name=record['event']
    if action_id is None:return 'boundary' if name in events else None
    # Current runtime rejections lack command identity. Surface uncertainty now.
    if name=='rejected':return 'unattributed_rejection'
    if name not in events:return None
    identity=record.get(FIELDS[name])
    if not isinstance(identity,str) or not identity:return 'identity_unknown'
    if name=='effect_evidence':
        effect=record.get('effect')
        if not isinstance(effect,dict) or effect.get('action_id')!=identity:return 'identity_conflict'
    if name=='independent_evaluation' and 'effect' in record:
        if not isinstance(record['effect'],dict) or record['effect'].get('action_id')!=identity:return 'identity_conflict'
    return 'boundary' if identity==action_id else None
