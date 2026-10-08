import json, pathlib, sys, statistics, copy
ORDER=['sleep','spin1','spin15','spin15','spin1','sleep']
def check(rows):
    assert len(rows)==192
    for k,r in enumerate(rows):
        b,i=divmod(k,32)
        assert (r['block'],r['i'],r['arm'])==(b,i,ORDER[b])
        assert r['deadline_ns']==r['block_start_ns']+(i+1)*20000000
        assert r['entry_ns']<=r['sleep_return_ns']<=r['observed_ns']
        assert r['lateness_ns']==r['observed_ns']-r['deadline_ns']>=0
        assert r['after']['process_cpu_ns']>=r['before']['process_cpu_ns']
        assert r['before']['schedstat'] is not None and r['after']['schedstat'] is not None
        assert r['before']['cpu_stat'] is not None and r['after']['cpu_stat'] is not None
        if i: assert r['block_start_ns']==rows[k-1]['block_start_ns']
    return True
p=pathlib.Path(sys.argv[1]); rows=[json.loads(s) for s in (p/'raw.jsonl').read_text().splitlines()]; check(rows)
controls=[]
for name in ['omit','late','identity']:
    bad=copy.deepcopy(rows)
    if name=='omit': bad.pop()
    if name=='late': bad[0]['lateness_ns']+=1
    if name=='identity': bad[0]['arm']='spin15'
    try: check(bad)
    except AssertionError: controls.append(name)
    else: raise RuntimeError('corruption accepted')
result={'disposition':'PASS_DIAGNOSTIC_CONSTRUCTION_ONLY','rows':len(rows),'rejected_mutations':controls,'arms':{}}
for arm in set(ORDER):
    rr=[r for r in rows if r['arm']==arm]; late=[r['lateness_ns'] for r in rr]
    result['arms'][arm]={'n':len(rr),'median_lateness_ns':statistics.median(late),'max_lateness_ns':max(late),'over_10ms':sum(x>10000000 for x in late),'measured_wait_cpu_ns':sum(r['after']['process_cpu_ns']-r['before']['process_cpu_ns'] for r in rr)}
pathlib.Path(sys.argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result))
