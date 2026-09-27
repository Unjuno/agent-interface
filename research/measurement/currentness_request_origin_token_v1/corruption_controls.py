import copy, json, pathlib, subprocess, sys, tempfile

def main(result_path,auditor_path,out_path):
    r=json.load(open(result_path)); cases=[]
    muts=[('digest',lambda x:x.__setitem__('transition_digest','0'*64)),('stale_install',lambda x:x.__setitem__('stale_response_installs',1)),('stale_admit',lambda x:x.__setitem__('stale_old_epoch_admissions',1)),('replay',lambda x:x.__setitem__('response_replay_installs',1)),('authority',lambda x:x.__setitem__('authority_promotions',1)),('decision',lambda x:x.__setitem__('decision','FAIL_STALE_RESPONSE_ESCAPE')),('invocations',lambda x:x.__setitem__('formal_invocations',2)),('pgen',lambda x:x.__setitem__('planner_generations_seen',[0]))]
    for name,fn in muts:
      z=copy.deepcopy(r); fn(z)
      with tempfile.TemporaryDirectory() as td:
        p=pathlib.Path(td)/'mut.json'; o=pathlib.Path(td)/'audit.json'; p.write_text(json.dumps(z))
        cp=subprocess.run([sys.executable,auditor_path,str(p),'--out',str(o)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        cases.append({'name':name,'rejected':cp.returncode!=0})
    out={'controls':cases,'rejected':sum(c['rejected'] for c in cases),'total':len(cases)}; assert out['rejected']==out['total']; pathlib.Path(out_path).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(out)
if __name__=='__main__': main(*sys.argv[1:])
