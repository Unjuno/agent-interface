from __future__ import annotations
PENDING='PENDING'; SATISFIED='SATISFIED'; UNKNOWN_ID='UNKNOWN_ID'; UNKNOWN_ORDER='UNKNOWN_ORDER'

def target_candidate(events,target='o1'):
    seen_a=False; last_seq=0
    prefix=[]
    terminal=None
    for e in events:
        if e.get('seq',0) <= last_seq:
            terminal=UNKNOWN_ORDER; prefix.append(terminal); break
        last_seq=e['seq']
        oid=e.get('obligation_id')
        if oid is None:
            terminal=UNKNOWN_ID; prefix.append(terminal); break
        if oid!=target:
            prefix.append(SATISFIED if terminal==SATISFIED else PENDING); continue
        if e['label']=='A': seen_a=True
        elif e['label']=='B' and seen_a: terminal=SATISFIED
        prefix.append(SATISFIED if terminal==SATISFIED else PENDING)
    return (terminal or PENDING),prefix

def unsafe_shared(events):
    seen_a=False; prefix=[]; terminal=None
    for e in events:
        if e['label']=='A': seen_a=True
        elif e['label']=='B' and seen_a: terminal=SATISFIED
        prefix.append(SATISFIED if terminal==SATISFIED else PENDING)
    return (terminal or PENDING),prefix
