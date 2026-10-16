"""Read admitted outcomes by their explicit originating request identity."""
ADMITTED={'accepted','terminal','effect_evidence','independent_evaluation'}
SUPPORTED=ADMITTED|{'command','rejected','finalization_status'}


def request_boundary(record,events,request_id):
    name=record['event']
    if name not in events and name!='rejected':return None
    if name in ADMITTED:
        metadata=record.get('admitted_request')
        if not isinstance(metadata,dict):return 'identity_unknown'
        action=record.get('id') if name in ('accepted','terminal') else record.get('final_program')
        if not isinstance(action,str) or metadata.get('declared_action_id')!=action:return 'identity_conflict'
        if 'effect' in record and (not isinstance(record['effect'],dict) or record['effect'].get('action_id')!=action):return 'identity_conflict'
        identity=metadata.get('transport_request_id')
    else:identity=record.get('transport_request_id')
    if not isinstance(identity,str) or not identity:return 'identity_unknown'
    if identity!=request_id:return None
    return 'request_rejected' if name=='rejected' and name not in events else 'boundary'
