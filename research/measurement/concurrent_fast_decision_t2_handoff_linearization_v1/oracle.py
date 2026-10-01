from __future__ import annotations

CLEAR='CLEAR'
HARD='HARD'

def evaluate_trace(spec: dict) -> dict:
    scope = spec['scope']
    generation = 1
    closed = False
    raw = None
    publish = None
    published_event = None
    consumed = set()
    effects = 0
    rows=[]
    prepared = {
        'decision_id': spec['decision_id'],
        'scope': scope,
        'generation': 1,
        'state': spec['state'],
        'prepared_ns': spec['prepared_ns'],
    }
    for op in spec['ops']:
        kind=op['kind']
        if kind=='RAW':
            n=op['ns']
            if raw is not None or not isinstance(n,int) or n<0: raise ValueError('oracle_raw')
            raw=n
        elif kind=='PUBLISH':
            n=op['ns']; eid=op['event_id']
            if raw is None or n<raw: raise ValueError('oracle_publish_clock')
            if published_event is None:
                publish=n; closed=True; generation += 1; published_event=eid
                rows.append({'kind':'publish','result':'PUBLISHED','ns':n})
            elif eid==published_event:
                rows.append({'kind':'publish','result':'DUPLICATE_NOOP','ns':n})
            else:
                raise ValueError('oracle_second_publication')
        elif kind=='ADMIT':
            c=op['ns']; ordinary=op['ordinary_authority']
            ps=op.get('presented_scope', prepared['scope'])
            pg=op.get('presented_generation', prepared['generation'])
            admitted=True; reason='ADMIT'
            if ps!=scope or prepared['scope']!=scope:
                admitted=False; reason='WRONG_SCOPE'
            elif not isinstance(pg,int) or pg<1:
                admitted=False; reason='BAD_GENERATION'
            elif prepared['decision_id'] in consumed:
                admitted=False; reason='REPLAY'
            elif publish is not None and c>=publish:
                admitted=False; reason='CLOSED_AFTER_PUBLICATION'
            elif closed:
                admitted=False; reason='CLOSED'
            elif pg!=generation or prepared['generation']!=generation:
                admitted=False; reason='STALE_OR_FORGED_GENERATION'
            elif prepared['state']!=CLEAR:
                admitted=False; reason='NONCLEAR_STATE'
            elif ordinary is not True:
                admitted=False; reason='ORDINARY_AUTHORITY_FALSE'
            if admitted:
                consumed.add(prepared['decision_id']); effects += 1
            rows.append({'kind':'admit','admitted':admitted,'reason':reason,'commit_ns':c,
                         'generation_at_commit':generation,'closed_at_commit':closed})
        else:
            raise ValueError('oracle_op')
    return {'rows':rows,'state':{'scope':scope,'generation':generation,'closed':closed,
            'raw_recv_return_ns':raw,'authority_publish_ns':publish,'published_event_id':published_event,
            'consumed_decisions':sorted(consumed),'effects':effects}}
