"""Construction-only reuse break-even probe for retained #3890 seed 3788."""
import argparse, hashlib, json, os, statistics, time
import torch
from loader import validate

PACKAGE='/inputs/skill.json'
EXPECTED='/inputs/expected.json'
OUT='/out/result.json'
GENERATION=3788
REQUESTS=1000

def instantiate(artifact, roles=None):
    models={}
    selected=artifact['tensors'] if roles is None else {r:artifact['tensors'][r] for r in roles}
    for role,state in selected.items():
        models[role]={k:torch.tensor(v,dtype=torch.float32) for k,v in state.items()}
    return models

def admit(req, artifact, digest):
    if req['role'] != req['scope_role']: raise ValueError('wrong_role_scope')
    if req['role'] not in artifact['tensors']: raise ValueError('unknown_role')
    if req['generation'] != artifact['generation']: raise ValueError('stale_generation')
    if req['package_digest'] != digest: raise ValueError('tampered_digest')

def score(model, role, row):
    x=torch.tensor([row],dtype=torch.float32)
    if role=='A':
        h=torch.tanh(torch.nn.functional.linear(x,model['enc.0.weight'],model['enc.0.bias']))
        y=torch.nn.functional.linear(h,model['head.weight'],model['head.bias'])
    else:
        h=torch.tanh(torch.nn.functional.linear(x,model['core.enc.0.weight'],model['core.enc.0.bias']))
        y=torch.nn.functional.linear(h,model['core.head.weight'],model['core.head.bias'])+h@model['a']@model['b']/2
    return [float(v) for v in y[0].tolist()],int(y.argmax(-1).item())

def load_validated(expected):
    return validate(PACKAGE,expected)

def sequence(artifact,digest,expected):
    roles=('A','B','C'); reqs=[]
    for i in range(REQUESTS):
        role=roles[i%3]; row=expected['roles'][role]['inputs'][i//3 % len(expected['roles'][role]['inputs'])]
        reqs.append({'role':role,'scope_role':role,'generation':GENERATION,'package_digest':digest,'input':row})
    return reqs

def run_reload(reqs,expected):
    rows=[]; parse_ns=instantiate_ns=infer_ns=0
    for req in reqs:
        t=time.perf_counter_ns(); artifact,digest=load_validated(expected); parse_ns+=time.perf_counter_ns()-t
        admit(req,artifact,digest)
        t=time.perf_counter_ns(); models=instantiate(artifact,(req['role'],)); instantiate_ns+=time.perf_counter_ns()-t
        t=time.perf_counter_ns(); logits,pred=score(models[req['role']],req['role'],req['input']); infer_ns+=time.perf_counter_ns()-t
        rows.append({'role':req['role'],'logits':logits,'prediction':pred})
    return rows,{'parse_validate_ns':parse_ns,'instantiate_ns':instantiate_ns,'inference_ns':infer_ns}

def run_reuse(reqs, expected):
    t=time.perf_counter_ns(); artifact,digest=load_validated(expected); parse_ns=time.perf_counter_ns()-t
    t=time.perf_counter_ns(); models=instantiate(artifact); init_ns=time.perf_counter_ns()-t
    rows=[]; infer_ns=0
    for req in reqs:
        admit(req,artifact,digest)
        t=time.perf_counter_ns(); logits,pred=score(models[req['role']],req['role'],req['input']); infer_ns+=time.perf_counter_ns()-t
        rows.append({'role':req['role'],'logits':logits,'prediction':pred})
    return rows,{'parse_validate_ns':parse_ns,'instantiate_ns':init_ns,'inference_ns':infer_ns}

def controls(artifact,digest,req):
    checks=[]; score_calls=0
    for name,changes in [('wrong_role_scope',{'scope_role':'B'}),('unknown_role',{'role':'Z','scope_role':'Z'}),('stale_generation',{'generation':GENERATION+1}),('tampered_digest',{'package_digest':'0'*64})]:
        probe=dict(req); probe.update(changes)
        try:
            admit(probe,artifact,digest)
            score_calls+=1; score(instantiate(artifact,(probe['role'],))[probe['role']],probe['role'],probe['input'])
            checks.append({'name':name,'outcome':'ACCEPT'})
        except ValueError as e: checks.append({'name':name,'outcome':'YIELD','reason':str(e)})
    return checks,score_calls

def main():
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    with open(PACKAGE,'rb') as f: before=hashlib.sha256(f.read()).hexdigest()
    with open(EXPECTED,encoding='utf-8') as f: expected=json.load(f)
    artifact,digest=load_validated(expected); reqs=sequence(artifact,digest,expected)
    a0=time.perf_counter_ns(); reload_rows,reload_stage=run_reload(reqs,expected); reload_total=time.perf_counter_ns()-a0
    b0=time.perf_counter_ns(); reuse_rows,reuse_stage=run_reuse(reqs,expected); reuse_total=time.perf_counter_ns()-b0
    control_rows,control_score_calls=controls(artifact,digest,reqs[0])
    with open(PACKAGE,'rb') as f: after=hashlib.sha256(f.read()).hexdigest()
    result={'status':'CONSTRUCTION_COMPLETE','kind':'construction-only','allocation':'needle-role-skill-reuse-break-even-3890-v1-20260928','package_sha256':before,'package_after_sha256':after,'expected_git_blob':'d1f982ecb142c1d6f59962b6b777615b8f1544b2','package_git_blob':'45b80150dac503f4eb6f3cb5d82f9afa2c587107','rows':len(reqs),'formal_blocks':0,'optimizer_steps':0,'network_calls':0,'retry':0,'decisions_equal':reload_rows==reuse_rows,'logits_exact':all(x['logits']==y['logits'] for x,y in zip(reload_rows,reuse_rows)),'predictions_equal':all(x['prediction']==y['prediction'] for x,y in zip(reload_rows,reuse_rows)),'reload_rows':reload_rows,'reuse_rows':reuse_rows,'reload_total_ns':reload_total,'reuse_total_ns':reuse_total,'reload_stage_ns':reload_stage,'reuse_stage_ns':reuse_stage,'controls':control_rows,'control_score_calls':control_score_calls,'environment':{'torch':torch.__version__,'device':'cpu','threads':torch.get_num_threads()}}
    with open(OUT,'w',encoding='utf-8') as f: json.dump(result,f,sort_keys=True,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('reload_rows','reuse_rows')},sort_keys=True))

if __name__=='__main__': main()
