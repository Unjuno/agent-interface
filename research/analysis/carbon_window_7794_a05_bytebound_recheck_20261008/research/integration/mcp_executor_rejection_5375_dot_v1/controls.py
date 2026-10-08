"""Data-only evidence corruptions; never executes a runtime operation."""
import copy
import hashlib
import json
from oracle import audit


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def controls(raw):
    cases = [
        ('missing_row', lambda x: x['rows'].pop()),
        ('forged_invoke_count', lambda x: x['rows'][1].update(invoke_entries=1)),
        ('rejected_artifact', lambda x: x['rows'][1].update(inventory={'unexpected': {'bytes': 1, 'sha256': 'a'*64}})),
        ('unhealthy_replacement', lambda x: x['health_probe'].update(completed=False)),
        ('native_tripwire', lambda x: x['tripwire_calls'].append('native')),
        ('source_change', lambda x: x.update(source_unchanged=False)),
        ('wrong_close_count', lambda x: x.update(public_close_calls=5)),
        ('false_recovery_success', lambda x: x['rows'][2]['result'].update(kind='return', value={
            'isError': False, 'content': [{'type': 'text', 'text': '{"status":"closed"}'}]})),
        ('nonboolean_authority', lambda x: x['rows'][0]['result']['value']['content'][0].update(
            text=json.dumps({'status':'closed','authority_granted':1}))),
        ('wrong_rejection', lambda x: x['rows'][1].update(result={'kind':'exception','type':'RuntimeError','message':'unrelated error'})),
        ('missing_profile', lambda x: x.pop('profile_events')),
        ('wrong_profile_operation', lambda x: x['profile_events'][0].update(operation='dispatch')),
    ]
    before = canonical(raw)
    records = []
    for name, mutate in cases:
        value = copy.deepcopy(raw)
        mutate(value)
        after = canonical(value)
        result = audit(value)
        records.append({'name': name, 'changed': before != after,
            'input_sha256': hashlib.sha256(after).hexdigest(), 'audit': result})
    return {'records': records,
            'passed': len(records) == 12 and all(x['changed'] and x['audit']['errors'] for x in records)}
