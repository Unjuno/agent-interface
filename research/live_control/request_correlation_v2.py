"""Runtime receive ordinal plus bounded caller-declared metadata; no authority."""
def correlation(sequence,command):
    result=dict(transport_request_id=None,runtime_request_sequence=sequence,declared_action_id=None,command_op=None,
                correlation_scope='current runtime input line; action ID is caller-declared')
    if isinstance(command,dict):
        transport=command.get('transport_request_id')
        if isinstance(transport,str) and 1<=len(transport)<=128:result['transport_request_id']=transport
        op=command.get('op')
        if isinstance(op,str) and len(op)<=64:result['command_op']=op
        identifier=command.get('id')
        if op in ('submit','cancel') and isinstance(identifier,str) and 1<=len(identifier)<=128:
            result['declared_action_id']=identifier
    return result
