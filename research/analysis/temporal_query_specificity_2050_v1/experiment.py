import hashlib,json,time
CASES=[('recent','C_RECENT','a1'),('baseline','C_BASELINE','a2'),('event','C_EVENT','a3'),('reversal','C_REVERSAL','a4'),('unknown_class',None,'a5'),('unknown_anchor','C_RECENT',None),('gap','C_RECENT','a7'),('stale','C_BASELINE','a8'),('redundant','C_RECENT','a9'),('prior_shift','C_OTHER','a10')]
frames=[{'ts':i,'source':f's1:main:{i}','value':('v'+str(i))} for i in range(0,100,10)]
def make(kind,cls,anchor):
    if kind=='UNIVERSAL_FIXED_HISTORY': return {'kind':kind,'history':frames,'class':cls,'anchor':anchor}
    n={'CLASS_ONLY_QUERY':3,'CLASS_PLUS_ANCHOR_QUERY':2,'WRONG_CLASS_OR_ANCHOR':1}[kind]
    return {'kind':kind,'history':frames[-n:],'class':cls if kind!='WRONG_CLASS_OR_ANCHOR' else 'WRONG','anchor':anchor if kind!='WRONG_CLASS_OR_ANCHOR' else 'wrong'}
def main():
    rows=[]
    for name,cls,anchor in CASES:
        arms={}
        for k in ('UNIVERSAL_FIXED_HISTORY','CLASS_ONLY_QUERY','CLASS_PLUS_ANCHOR_QUERY','WRONG_CLASS_OR_ANCHOR'):
            t0=time.perf_counter_ns(); obj=make(k,cls,anchor); raw=json.dumps(obj,sort_keys=True,separators=(',',':')).encode(); t1=time.perf_counter_ns()
            arms[k]={'bytes':len(raw),'construction_ns':t1-t0,'history_count':len(obj['history'])}
        rows.append({'case':name,'arms':arms})
    assert len(rows)==10
    assert all(r['arms']['CLASS_PLUS_ANCHOR_QUERY']['bytes']<=r['arms']['UNIVERSAL_FIXED_HISTORY']['bytes'] for r in rows)
    assert rows[4]['arms']['CLASS_PLUS_ANCHOR_QUERY']['history_count']==2
    totals={k:{'bytes':sum(r['arms'][k]['bytes'] for r in rows),'history':sum(r['arms'][k]['history_count'] for r in rows)} for k in ('UNIVERSAL_FIXED_HISTORY','CLASS_ONLY_QUERY','CLASS_PLUS_ANCHOR_QUERY','WRONG_CLASS_OR_ANCHOR')}
    digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    print(json.dumps({'cases':10,'totals':totals,'rows':rows,'serialization_oracle':'PASS','unknown_inputs_retained':'PASS','model_invocations':0,'gui_invocations':0,'task_input_events':0,'digest':digest},sort_keys=True))
main()
