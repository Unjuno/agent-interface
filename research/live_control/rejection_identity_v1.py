"""Attribute rejection without interpreting diagnostic text as execution evidence."""
def rejected(command, used_ids, error):
    result = {'event': 'rejected', 'reason': str(error), 'admission': 'unknown'}
    if not isinstance(command, dict): return result
    for field in ('op', 'id', 'transport_request_id'):
        value = command.get(field)
        if type(value) is str and value: result[field] = value
    if (result.get('op') == 'submit' and 'id' in result
            and 'transport_request_id' in result and result['id'] not in used_ids):
        result['admission'] = 'not_admitted'
    return result
