from __future__ import annotations
from collections import defaultdict
import hashlib,json
from representation import full_signature,id_invariant_signature,normalized_dispositions


def analyze(rows):
    full=defaultdict(set); inv=defaultdict(set); members=defaultdict(list)
    for r in rows:
        y=normalized_dispositions(r)
        full[full_signature(r)].add(y)
        s=id_invariant_signature(r); inv[s].add(y); members[s].append(r['row_id'])
    full_conf={k:v for k,v in full.items() if len(v)>1}
    inv_conf={k:v for k,v in inv.items() if len(v)>1}
    witnesses=[]
    for k in sorted(inv_conf):
        witnesses.append({'signature':json.loads(k),'row_ids':sorted(members[k]),'distinct_acceptable_sets':len(inv_conf[k])})
    return {'full_conflicting_groups':len(full_conf),'id_invariant_conflicting_groups':len(inv_conf),'id_invariant_witnesses':witnesses}
