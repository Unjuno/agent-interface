"""Pure proposals for a synthetic claim register; no I/O or authority grant."""
import copy
import hashlib
import json

FIELDS = {'task_id', 'owner', 'scope', 'successor', 'question_key'}
REGISTER_FIELDS = {'schema', 'case', 'revision', 'claims', 'consumed_task_ids', 'fixture_only'}


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n'


def blob(text):
    raw = text.encode('utf-8')
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def validate_claim(claim):
    if type(claim) is not dict or set(claim) != FIELDS:
        raise ValueError('claim fields')
    if any(type(v) is not str or not v or v.strip() != v for v in claim.values()):
        raise ValueError('claim values')
    if not claim['scope'].startswith('research/synthetic/') or not claim['scope'].endswith('/**'):
        raise ValueError('fixture scope')
    parts = claim['scope'][:-3].split('/')
    if any(p in ('', '.', '..') or any(c in p for c in '*?[]\\') for p in parts):
        raise ValueError('noncanonical scope')


def conflicts(left, right):
    reasons = [k for k in ('task_id', 'scope') if left[k] == right[k]]
    if (left['successor'], left['question_key']) == (right['successor'], right['question_key']):
        reasons.append('semantic_successor')
    return reasons


def validate_register(current):
    if type(current) is not dict or set(current) != REGISTER_FIELDS:
        raise ValueError('register fields')
    if current['schema'] != 'claim-merge-fixture-v1' or current['fixture_only'] is not True:
        raise ValueError('not a fixture')
    if type(current['case']) is not str or not current['case']:
        raise ValueError('case')
    if type(current['revision']) is not int or current['revision'] < 0:
        raise ValueError('revision')
    claims, consumed = current['claims'], current['consumed_task_ids']
    if type(claims) is not list or type(consumed) is not list:
        raise ValueError('lists')
    if any(type(x) is not str or not x for x in consumed) or len(set(consumed)) != len(consumed):
        raise ValueError('consumed identities')
    for i, claim in enumerate(claims):
        validate_claim(claim)
        if claim['task_id'] in consumed or any(conflicts(claim, c) for c in claims[:i]):
            raise ValueError('inconsistent current register')


def propose(current, candidate, recoveries_used=0):
    """Caller supplies read bytes. A proposal alone is never registration.

    Initial proposal and first recovery use recoveries_used=0. After that
    recovery PUT, any further proposal uses 1 and stops. HTTP is outside here.
    """
    try:
        if type(recoveries_used) is not int or recoveries_used < 0:
            raise ValueError('recovery count')
        validate_register(current)
        validate_claim(candidate)
    except (ValueError, KeyError, TypeError) as error:
        return {'status': 'INVALID', 'reason': str(error), 'grants_authority': False}
    if recoveries_used >= 1:
        return {'status': 'STOP_CONTENDED', 'grants_authority': False}
    reasons = ['consumed_task_id'] if candidate['task_id'] in current['consumed_task_ids'] else []
    for existing in current['claims']:
        reasons.extend(conflicts(candidate, existing))
    if reasons:
        return {'status': 'CONFLICT', 'reasons': sorted(set(reasons)), 'grants_authority': False}
    updated = copy.deepcopy(current)
    updated['revision'] += 1
    updated['claims'].append(copy.deepcopy(candidate))
    return {'status': 'PROPOSE', 'document': updated, 'grants_authority': False}
