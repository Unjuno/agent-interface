"""Closed typed JSON event-prefix oracle; no candidate or frozen auditor import."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re

SOURCE='9f389bf99882f7107ff41902474e9e2d6699667b65eabcd5cd5b7f97f1e158ba'
SCHEMA='6501-cancel-order-boundary-v1'
EXPECTED_COUNTS={'retained_timestamp_lt':{'wrong_admit':48,'wrong_reject':0},
                 'conservative_timestamp_le':{'wrong_admit':0,'wrong_reject':48},
                 'ordered':{'wrong_admit':0,'wrong_reject':0}}

def same_json(actual,expected):
    if type(actual) is not type(expected):return False
    if type(expected) is dict:
        return actual.keys()==expected.keys() and all(same_json(actual[k],v) for k,v in expected.items())
    if type(expected) is list:
        return len(actual)==len(expected) and all(same_json(a,b) for a,b in zip(actual,expected))
    return actual==expected

def audit(raw,expected_source=SOURCE):
    errors=[]
    counts={name:{'wrong_admit':0,'wrong_reject':0} for name in EXPECTED_COUNTS}
    result={'errors':errors,'counts':counts,'assignments':0,'waiter_decisions':0}
    if type(expected_source) is not str or re.fullmatch('[0-9a-f]{64}',expected_source) is None:
        errors.append('expected-source-type');return result
    if type(raw) is not dict or set(raw)!={'schema','source_sha256','rows'}:
        errors.append('root-schema');return result
    if type(raw['schema']) is not str or raw['schema']!=SCHEMA or type(raw['source_sha256']) is not str or raw['source_sha256']!=expected_source:
        errors.append('source/schema');return result
    rows=raw['rows']
    if type(rows) is not list:
        errors.append('rows-type');return result
    result['assignments']=len(rows);result['waiter_decisions']=len(rows)*2
    domain=itertools.product(('TRUE','FALSE'),(None,4,5,6),(None,4,5,6),itertools.permutations(('cancel_a','cancel_b','return')))
    if len(rows)!=192:
        errors.append('denominator');return result
    for index,(row,(truth,ca,cb,order)) in enumerate(zip(rows,domain)):
        schedule={'cancel_a':ca,'cancel_b':cb,'return':5}
        events=[[actor,schedule[actor],rank] for rank,actor in enumerate(order) if schedule[actor] is not None]
        timeline=sorted(events,key=lambda e:(e[1],e[2]))
        before=set()
        for actor,clock,rank in timeline:
            if actor=='return':break
            before.add(actor.removeprefix('cancel_'))
        outcomes={}
        for caller,cancel in [('a',ca),('b',cb)]:
            reference='CANCELLED_WAITER' if caller in before else 'ADMISSIBLE_'+truth
            predictions={'ordered':reference,
                         'retained_timestamp_lt':'CANCELLED_WAITER' if cancel is not None and cancel<5 else 'ADMISSIBLE_'+truth,
                         'conservative_timestamp_le':'CANCELLED_WAITER' if cancel is not None and cancel<=5 else 'ADMISSIBLE_'+truth}
            outcomes[caller]=predictions
            for mode,verdict in predictions.items():
                if verdict!=reference:counts[mode]['wrong_admit' if reference=='CANCELLED_WAITER' else 'wrong_reject']+=1
        expected={'id':index,'truth':truth,'cancel_a':ca,'cancel_b':cb,'events':events,'outcomes':outcomes}
        if not same_json(row,expected):errors.append('typed-row:'+str(index))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('--expected-raw-sha256',required=True)
    p.add_argument('--source-sha256',default=SOURCE);p.add_argument('--output',required=True);a=p.parse_args()
    data=Path(a.raw).read_bytes();digest=hashlib.sha256(data).hexdigest()
    if digest!=a.expected_raw_sha256:
        result={'errors':['raw-byte-hash'],'raw_sha256':digest,'disposition':'FAIL_RETAINED_AUDIT_V2'}
    else:
        try:raw=json.loads(data)
        except (ValueError,UnicodeDecodeError):raw=None
        result=audit(raw,a.source_sha256);result['raw_sha256']=digest
        good=not result['errors'] and same_json(result['counts'],EXPECTED_COUNTS)
        result['disposition']='PASS_RETAINED_CANCEL_ORDER_V2_SCOPED' if good else 'FAIL_RETAINED_AUDIT_V2'
    with Path(a.output).open('x',encoding='utf8',newline='\n') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(result,sort_keys=True))
    return 0 if result['disposition']=='PASS_RETAINED_CANCEL_ORDER_V2_SCOPED' else 1
if __name__=='__main__':raise SystemExit(main())
