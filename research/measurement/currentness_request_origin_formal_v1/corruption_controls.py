import copy,json,sys
from auditor import validate

def main(result_path,audit_path,out_path):
    r=json.load(open(result_path)); a=json.load(open(audit_path)); exp=a['regenerated']
    muts=[('digest',lambda x:x.__setitem__('transition_digest','0'*64)),('stale',lambda x:x.__setitem__('stale_response_installs',1)),('stress',lambda x:x.__setitem__('stress_refused',x['stress_refused']-1)),('replay',lambda x:x.__setitem__('response_replay_rebinds',1)),('authority',lambda x:x.__setitem__('authority_promotions',1)),('decision',lambda x:x.__setitem__('decision','FAIL_STALE_RESPONSE_ESCAPE_FORMAL')),('invocation',lambda x:x.__setitem__('primary_invocations',2)),('pgen',lambda x:x.__setitem__('planner_generations_seen',[0]))]
    rows=[]
    for name,fn in muts:
        z=copy.deepcopy(r); fn(z); rows.append({'name':name,'rejected':bool(validate(z,exp))})
    out={'controls':rows,'rejected':sum(x['rejected'] for x in rows),'total':len(rows)}; assert out['rejected']==out['total']; open(out_path,'w').write(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main(*sys.argv[1:])
