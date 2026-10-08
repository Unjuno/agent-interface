"""Bounded, atomic in-memory semantics. Not the production runtime."""
import json

ARMS = ('NO_CROSS_PRODUCER', 'COMMON_WORK_ID', 'ONE_PER_GENERATION', 'SEMANTIC')
FIELDS = ('session', 'revision', 'generation', 'target', 'incarnation', 'operation', 'opportunity', 'params')
CAPACITY = 16

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

def simulate(arm, events):
    assert arm in ARMS
    state = dict(generation=1, incarnations={'save':1, 'next':1, 'other':1}, revisions=[1,2], revoked=False)
    retries, records, generations = {}, {}, set()
    decisions, held, peak = [], False, 0
    for event in events:
        if event['kind'] == 'transition':
            state.update(event['update'])
            continue
        if event['kind'] == 'release':
            held = False
            decisions.append(dict(status='RELEASED', effect=0, coalesced_to=None, held=False))
            continue
        p, now = event['proposal'], event['now']
        row = dict(status=None, effect=0, coalesced_to=None, held=False)
        # Admission precedes any reuse; previous success never lends authority.
        if state['revoked'] or not p['authorized']:
            row['status'] = 'REJECT_AUTHORITY'
        elif now > p['deadline']:
            row['status'] = 'REJECT_EXPIRED'
        elif p['identity'] != 'exact' or any(p.get(k) is None for k in FIELDS) or not p.get('producer') or not p.get('retry_intent'):
            row['status'] = 'YIELD_IDENTITY'
        elif p['generation'] != state['generation'] or p['revision'] not in state['revisions'] or state['incarnations'].get(p['target']) != p['incarnation']:
            row['status'] = 'REJECT_STALE'
        elif event.get('postcondition_satisfied', False):
            row['status'] = 'SUPERSEDED'
        else:
            fingerprint = canonical([p[k] for k in FIELDS])
            retry_key = (p['session'], p['producer'], p['retry_intent'])
            if retry_key in retries:
                old_fp, first = retries[retry_key]
                row['status'] = 'RETRY_KNOWN' if old_fp == fingerprint else 'REJECT_RETRY_CONFLICT'
                row['coalesced_to'] = first if old_fp == fingerprint else None
            else:
                if arm == 'COMMON_WORK_ID':
                    key = (p['session'], p['common_work_id']) if p.get('common_work_id') else None
                elif arm == 'SEMANTIC':
                    key = fingerprint
                else:
                    key = None
                if arm == 'COMMON_WORK_ID' and key is None:
                    row['status'] = 'YIELD_COMMON_ID'
                elif key is not None and key in records:
                    old_fp, first = records[key]
                    row['status'] = 'COALESCED' if old_fp == fingerprint else 'REJECT_COMMON_CONFLICT'
                    row['coalesced_to'] = first if old_fp == fingerprint else None
                elif arm == 'ONE_PER_GENERATION' and (p['session'],p['generation']) in generations:
                    row['status'] = 'YIELD_GENERATION_USED'
                elif len(retries) >= CAPACITY or len(records) >= CAPACITY:
                    row['status'] = 'YIELD_CAPACITY'
                else:
                    row['status'], row['effect'] = 'EXECUTED', 1
                    first = len(decisions)
                    retries[retry_key] = (fingerprint, first)
                    if key is not None: records[key] = (fingerprint, first)
                    generations.add((p['session'],p['generation']))
                    held = True
                    # Atomic bounded click completes with unconditional release.
                    held = False
                # Cross-producer reuse is also a known retry outcome for this producer.
                if row['status'] == 'COALESCED':
                    retries[retry_key] = (fingerprint,row['coalesced_to'])
        row['held'] = held
        decisions.append(row)
        peak = max(peak, len(retries)+len(records)+len(generations))
    held = False  # terminal cleanup independent of proposal dispositions
    return dict(decisions=decisions, neutral=not held, authority_created=0, peak_entries=peak)
