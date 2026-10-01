from __future__ import annotations
import json


def full_signature(row):
    return json.dumps(row['candidate_input'],sort_keys=True,separators=(',',':'))


def id_invariant_packet(packet):
    return {
        'intent_id': packet['intent_id'],
        'state_epoch': packet['state_epoch'],
        'binding_id': packet['binding_id'],
        'allowed_operations': list(packet['allowed_operations']),
        'payload_ref_present': packet['payload_ref_present'],
        'candidates': [
            {'role': c['role'], 'ops': list(c['ops'])}
            for c in packet['candidates']
        ],
    }


def id_invariant_signature(row):
    return json.dumps(id_invariant_packet(row['candidate_input']),sort_keys=True,separators=(',',':'))


def normalized_dispositions(row):
    candidates=row['candidate_input']['candidates']
    index={c['id']:i for i,c in enumerate(candidates)}
    out=[]
    for d in row['acceptable']:
        n={'op':d['op']}
        if 'reason' in d:n['reason']=d['reason']
        if 'payload_ref' in d:n['payload_ref_present']=True
        if 'target' in d:
            if d['target'] not in index: raise ValueError('oracle target absent from candidate set')
            n['target_slot']=index[d['target']]
        out.append(n)
    return tuple(sorted(json.dumps(x,sort_keys=True,separators=(',',':')) for x in out))
