import json
OPS=('CLICK','TYPE_TEXT','SCROLL')
D=('ACTION_SET','WATCH','NO_LOCAL_ACTION','YIELD','DONE_CANDIDATE')

def good(x): return isinstance(x,str) and len(x.strip())>0
def dump(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def row_valid(r):
    if not isinstance(r,dict) or sorted(r)!=sorted(['row_id','episode_id','split_group','split','model_visible','oracle','grants_input_authority']): return False
    if not good(r.get('row_id')) or not good(r.get('episode_id')) or not good(r.get('split_group')) or r.get('split') not in ('train','eval') or r.get('grants_input_authority') is not False:return False
    m=r.get('model_visible'); o=r.get('oracle')
    if not isinstance(m,dict) or sorted(m)!=sorted(['intent_id','observation_ref','observation_epoch','allowed_operations','targets','payload_refs','prior_receipt_refs']):return False
    if not good(m.get('intent_id')) or not good(m.get('observation_ref')) or type(m.get('observation_epoch')) is not int or m['observation_epoch']<0:return False
    a=m.get('allowed_operations'); ts=m.get('targets'); ps=m.get('payload_refs'); rs=m.get('prior_receipt_refs')
    if not isinstance(a,list) or not a or len(set(a))!=len(a) or any(x not in OPS for x in a):return False
    if not isinstance(ts,list) or not isinstance(ps,list) or not isinstance(rs,list) or len(ps)!=len(set(ps)) or any(not good(x) for x in ps+rs):return False
    tm={}
    for t in ts:
        if not isinstance(t,dict) or sorted(t)!=sorted(['target_id','observation_ref','observation_epoch','operations']):return False
        tid=t.get('target_id'); tops=t.get('operations')
        if not good(tid) or tid in tm or t.get('observation_ref')!=m['observation_ref'] or t.get('observation_epoch')!=m['observation_epoch']:return False
        if not isinstance(tops,list) or not tops or len(set(tops))!=len(tops) or any(x not in a for x in tops):return False
        tm[tid]=set(tops)
    if not isinstance(o,dict) or sorted(o)!=sorted(['disposition','acceptable_actions','oracle_source_ref','independent','postdecision_refs','done_verifier_ref']):return False
    if o.get('disposition') not in D or not good(o.get('oracle_source_ref')) or o.get('independent') is not True:return False
    if not isinstance(o.get('postdecision_refs'),list) or any(not good(x) for x in o['postdecision_refs']):return False
    acts=o.get('acceptable_actions')
    if not isinstance(acts,list):return False
    if o['disposition']=='ACTION_SET':
        if not acts or o.get('done_verifier_ref') is not None:return False
        seen=set()
        for p in acts:
            if not isinstance(p,dict):return False
            op=p.get('operation'); tid=p.get('target_id')
            if op not in OPS or op not in a or not good(tid) or tid not in tm or op not in tm[tid]:return False
            if op=='CLICK' and set(p)!= {'operation','target_id'}:return False
            if op=='TYPE_TEXT' and (set(p)!= {'operation','target_id','payload_ref'} or not good(p.get('payload_ref')) or p['payload_ref'] not in ps):return False
            if op=='SCROLL' and (set(p)!= {'operation','target_id','delta'} or type(p.get('delta')) is not int or p['delta']==0 or not -3<=p['delta']<=3):return False
            z=dump(p)
            if z in seen:return False
            seen.add(z)
    elif o['disposition']=='DONE_CANDIDATE':
        if acts or not good(o.get('done_verifier_ref')):return False
    else:
        if acts or o.get('done_verifier_ref') is not None:return False
    return True

def dataset_valid(rows):
    if not isinstance(rows,list) or not rows:return False
    ids=set(); es={}; gs={}
    for r in rows:
        if not row_valid(r) or r['row_id'] in ids:return False
        ids.add(r['row_id'])
        for k,m in ((r['episode_id'],es),(r['split_group'],gs)):
            if k in m and m[k]!=r['split']:return False
            m[k]=r['split']
    return True
