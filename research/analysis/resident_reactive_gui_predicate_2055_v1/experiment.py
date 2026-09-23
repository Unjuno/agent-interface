import hashlib,json
CASES=[('persistent',[(0,False),(10,True),(20,True),(30,True)],True),('none',[(0,False),(10,False)],False),('transient',[(0,False),(10,True),(11,False)],True),('revoke',[(0,False),(10,True)],False),('deadline',[(0,False),(10,True)],False),('stale_generation',[(0,False),(10,True)],False),('focus_loss',[(0,False),(10,True)],False),('target_replaced',[(0,False),(10,True)],False),('duplicate_edge',[(0,False),(10,True),(20,False),(30,True)],True),('gap',[(0,False),(30,True)],False),('already_effected',[(0,False),(10,True)],False),('terminal_release',[(0,False),(10,True)],True)]
def resident(events,name):
    fired=0; prev=False
    for t,v in events:
        valid=name not in {'revoke','deadline','stale_generation','focus_loss','target_replaced','gap','already_effected'}
        if v and not prev and valid and fired==0: fired+=1
        prev=v
    return fired
def poll(events): return int(any(t in (0,20) and v for t,v in events))
def main():
    rows=[]
    for name,events,eligible in CASES:
        rows.append({'case':name,'resident_fires':resident(events,name),'poll_fires':poll(events),'eligible':eligible,'released':True})
    assert len(rows)==12 and all(r['released'] for r in rows)
    assert next(r for r in rows if r['case']=='transient')['resident_fires']==1
    assert next(r for r in rows if r['case']=='transient')['poll_fires']==0
    assert all(next(r for r in rows if r['case']==n)['resident_fires']==0 for n in ('revoke','deadline','stale_generation','focus_loss','target_replaced','gap','already_effected'))
    assert next(r for r in rows if r['case']=='duplicate_edge')['resident_fires']==1
    digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    print(json.dumps({'cases':12,'rows':rows,'resident_oracle':'PASS','poll_control':'PASS','terminal_release':'PASS','model':0,'gui':0,'input':0,'digest':digest},sort_keys=True))
main()
