"""Append MCP response projections and run frozen pure policy, without network I/O."""
import json
import sys
from pathlib import Path
import policy
ROOT=Path(__file__).resolve().parent
PLAN=json.loads((ROOT/'plan.json').read_text())
DATA=ROOT/'evidence.json'

def save(d):
    DATA.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')

def read(d,name,label,content,sha,ref):
    if policy.blob(content)!=sha: raise ValueError('read content/SHA mismatch')
    row=next(r for r in d['cases'] if r['name']==name)
    row[label]={'content':content,'sha':sha,'ref':ref}
    if label=='recovery_read':
        candidate=next(c['candidate'] for c in PLAN['cases'] if c['name']==name)
        result=policy.propose(json.loads(content),PLAN['claims'][candidate],0)
        row['recovery_policy_status']=result['status'];row['recovery_reasons']=result.get('reasons',[])
        row['local_recovery_result']=result
        print(json.dumps(result,sort_keys=True))
        if result['status']=='PROPOSE': print(policy.encode(result['document']),policy.blob(policy.encode(result['document'])))
    save(d)

if __name__=='__main__':
    x=json.load(sys.stdin)
    if x['op']=='init':
        if DATA.exists():raise ValueError('allocation evidence already exists')
        d={'task':PLAN['task'],'freeze_commit':'6fa89190a1f80065a13a1f000aae3c7dd4f8d53a',
           'provenance':'Exact content/SHA and update result fields transcribed from MCP responses; not raw HTTP headers or independently authenticated server logs.',
           'cases':[dict(name=c['name'],writes=[],grants_real_authority=False) for c in PLAN['cases']]}
        save(d)
    else:d=json.loads(DATA.read_text())
    if x['op']=='read':read(d,x['name'],x['label'],x['content'],x['sha'],x['ref'])
    elif x['op']=='write':
        row=next(r for r in d['cases'] if r['name']==x['name'])
        w={k:x[k] for k in ('step','content','expected_sha','response')}
        if any(a['step']==w['step'] for a in row['writes']):raise ValueError('duplicate log step')
        if w['response']['kind']=='success' and policy.blob(w['content'])!=w['response']['content_sha']:raise ValueError('write SHA mismatch')
        row['writes'].append(w);save(d)
    elif x['op']=='terminal':
        row=next(r for r in d['cases'] if r['name']==x['name'])
        row['terminal']=x['terminal']
        if x['terminal']=='STOP_CONTENDED':
            result=policy.propose(json.loads(row['final_read']['content']),PLAN['claims']['B'],1)
            if result['status']!='STOP_CONTENDED':raise ValueError('budget failed')
            row['budget_result']=result
        save(d)
