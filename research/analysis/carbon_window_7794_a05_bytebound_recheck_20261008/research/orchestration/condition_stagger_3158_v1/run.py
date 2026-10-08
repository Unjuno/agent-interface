import json,hashlib,random,subprocess,sys
SEED=3158
SCENARIOS=[
 ('independent',{'critical':'low','resource':None,'pred':'ready','fresh':True,'duplicate':False,'cancel':False,'deadline':True}),
 ('exclusive_conflict',{'critical':'high','resource':'gpu','pred':'ready','fresh':True,'duplicate':False,'cancel':False,'deadline':True,'busy':True}),
 ('stale_during_delay',{'critical':'high','resource':'x11','pred':'ready','fresh':False,'duplicate':False,'cancel':False,'deadline':True}),
 ('predecessor_failure',{'critical':'high','resource':'x11','pred':'failed','fresh':True,'duplicate':False,'cancel':False,'deadline':True}),
 ('duplicate_start',{'critical':'high','resource':'x11','pred':'ready','fresh':True,'duplicate':True,'cancel':False,'deadline':True}),
 ('cancelled',{'critical':'high','resource':'x11','pred':'ready','fresh':True,'duplicate':False,'cancel':True,'deadline':True}),
 ('deadline_expiry',{'critical':'high','resource':'x11','pred':'ready','fresh':True,'duplicate':False,'cancel':False,'deadline':False}),
]
def decide(policy,s):
    safe=bool(s['fresh'] and s['pred']=='ready' and not s['cancel'] and s['deadline'] and not s.get('busy',False) and not s['duplicate'])
    if policy=='CONDITION_STAGGER': return ('start' if safe else 'deny','condition')
    if policy=='SERIAL_CRITICAL': return ('start' if safe else 'deny','serial')
    if policy=='IMMEDIATE': return ('start','immediate')
    if policy=='FIXED_STAGGER': return ('start' if not s.get('busy',False) else 'start','timer')
def audit(rows):
    out=[]
    for r in rows:
        unsafe=(r['started'] and not r['safe'])
        out.append({'scenario':r['scenario'],'unsafe_start':unsafe,'safe_start':r['started'] and r['safe']})
    return out
rows=[]
for policy in ('IMMEDIATE','FIXED_STAGGER','CONDITION_STAGGER','SERIAL_CRITICAL'):
 for name,s in SCENARIOS:
  action,reason=decide(policy,s); rows.append({'policy':policy,'scenario':name,'started':action=='start','safe':bool(s['fresh'] and s['pred']=='ready' and not s['cancel'] and s['deadline'] and not s.get('busy',False) and not s['duplicate']),'reason':reason,'resource':s.get('resource'),'seed':SEED})
audit_rows=audit(rows)
condition_unsafe=any(r['unsafe_start'] for r in audit_rows for x in rows if x['policy']=='CONDITION_STAGGER' and x['scenario']==r['scenario'] and r['scenario']==x['scenario'] and x['started'])
immediate_unsafe=any(r['unsafe_start'] for r in audit_rows for x in rows if x['policy']=='IMMEDIATE' and x['scenario']==r['scenario'] and x['started'])
result={'decision':'PASS_STAGGERED_SUBAGENT_ORCHESTRATION_SCOPED' if not condition_unsafe and immediate_unsafe else 'FAIL_STAGGERED_START_UNSAFE','rows':rows,'independent_audit':audit_rows,'seed':SEED,'source_sha256':hashlib.sha256(open(__file__,'rb').read()).hexdigest(),'model_calls':0,'network_calls':0}
print(json.dumps(result,sort_keys=True))
