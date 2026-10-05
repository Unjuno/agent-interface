"""Directed copies of saved data only; no producer or transport imports."""
import copy
import hashlib
import json


def wire_alias(raw, value, tags):
    changed = copy.deepcopy(raw)
    events = 0
    for event in changed['trials'][0]['server_events']:
        if event['call_id'] == 'rpc-0' and event['event'] in tags:
            payload = json.loads(bytes.fromhex(event['wire_hex']))
            payload['answer'] = value
            data = (json.dumps(payload, sort_keys=True, separators=(',', ':')) + '\n').encode()
            event['wire_hex'] = data.hex()
            event['sha256'] = hashlib.sha256(data).hexdigest()
            events += 1
    if events != len(tags):
        raise ValueError('ineffective alias control')
    return changed


def mutations(raw):
    rows = []
    data = copy.deepcopy(raw); data['trials'].pop()
    rows.append(('missing_trial', 'missing trial', data, False))
    data = copy.deepcopy(raw); data['trials'][-1] = copy.deepcopy(data['trials'][0])
    rows.append(('duplicate_trial', 'trial coverage', data, False))
    data = copy.deepcopy(raw); data['trials'][0]['callers'].pop()
    rows.append(('missing_waiter', 'missing waiter', data, False))
    data = copy.deepcopy(raw)
    trial = next(t for t in data['trials'] if t['case_id'] == 'different_target' and t['mode'] == 'predicate_inflight')
    trial['callers'][1]['descriptive_match'] = True
    rows.append(('wrong_scope_claim', 'per-waiter descriptive gate', data, False))
    data = copy.deepcopy(raw); data['trials'][0]['server_events'][0]['sha256'] = '0' * 64
    rows.append(('wire_hash', 'wire hash/bound', data, False))
    data = copy.deepcopy(raw); data['trials'][0]['active_server_threads_after_cleanup'] = False
    rows.append(('cleanup_bool_alias', 'cleanup', data, False))
    data = copy.deepcopy(raw); data['trials'][0]['callers'][0]['authority'] = True
    rows.append(('unknown_authority', 'caller schema', data, False))
    data = copy.deepcopy(raw); data['trials'][0]['server_events'].pop()
    rows.append(('omitted_event', 'complete transport triples', data, False))
    for value in (1, 1.0):
        for tags in ({'server_sent'}, {'client_received'}, {'server_sent', 'client_received'}):
            name = 'wire_answer_' + type(value).__name__ + '_' + '_'.join(sorted(tags))
            rows.append((name, 'typed wire binding', wire_alias(raw, value, tags), True))
    return rows
