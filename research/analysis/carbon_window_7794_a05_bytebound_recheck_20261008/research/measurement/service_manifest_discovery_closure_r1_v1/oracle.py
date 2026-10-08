from __future__ import annotations
REQUIRED=(
 'service_identity','protocol_identity','control','observation','operation_schema','capability_snapshot',
 'observation_catalog','events','authority','freshness','handback','fallback')
REL={'control':'control','observation':'observation','operation_schema':'operation_schema','capability_snapshot':'capability_snapshot','observation_catalog':'observation_catalog','events':'events'}
SEM={'authority':'authority','freshness':'freshness','handback':'handback'}
def okstr(x): return type(x) is str and len(x)>0
def inspect(m):
    if type(m) is not dict:return {'status':'INVALID','errors':['manifest_type'],'values':{}}
    e=[];v={}
    if 'session_capabilities' in m:e.append('forbidden_session_state')
    s=m.get('service',None)
    if type(s) is dict and okstr(s.get('id')):v['service_identity']=s['id']
    else:e.append('service_identity')
    p=m.get('protocol',None)
    if type(p) is dict and okstr(p.get('id')) and type(p.get('major')) is int:
        if p['major']==1:v['protocol_identity']=(p['id'],p['major'])
        else:e.append('protocol_major')
    else:e.append('protocol_identity')
    r=m.get('relations',None)
    for q,k in REL.items():
        if type(r) is dict and okstr(r.get(k)):v[q]=r[k]
        else:e.append(q)
    s2=m.get('semantics',None)
    for q,k in SEM.items():
        if type(s2) is dict and okstr(s2.get(k)):v[q]=s2[k]
        else:e.append(q)
    if okstr(m.get('fallback')):v['fallback']=m['fallback']
    else:e.append('fallback')
    return {'status':'PASS' if not e and len(v)==12 else 'INVALID','errors':sorted(set(e)),'values':v}
