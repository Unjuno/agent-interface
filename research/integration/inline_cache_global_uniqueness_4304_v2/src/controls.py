"""Prospective, effective, copied-evidence corruptions; never edit formal raw."""
from __future__ import annotations
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
from audit import analyze, load

def run(records, construction=False, sources=None):
    stable=next(i for i,r in enumerate(records) if r['raw']['scenario']=='STABLE' and r['raw']['arm']=='LOCAL_PATCH')
    duplicate=next(i for i,r in enumerate(records) if r['raw']['scenario']=='DUPLICATE' and r['raw']['arm']=='GLOBAL_UNIQUENESS')
    def mutate(name, rr):
        r=rr[stable]['raw']; q=rr[duplicate]['raw']
        if name=='missing_case':rr.pop()
        elif name=='duplicate_case':rr.append(copy.deepcopy(rr[0]))
        elif name=='wrong_point':r['warm']['response']['point'][0]+=1
        elif name=='stale_binding':r['warm']['request']['binding']['generation']=2
        elif name=='authority_grant':r['warm']['response']['authority_granted']=True
        elif name=='missing_release':r['input'].pop()
        elif name=='held_button':r['post_neutral']['button_mask']=256
        elif name=='missing_effect':rr[stable]['journal']=[j for j in rr[stable]['journal'] if j['kind']!='effect']
        elif name=='source_identity':r['sources']['study.py']='0'*64
        elif name=='scorer_pixel_rehashed':
            im=q['witness'];b=bytearray(base64.b64decode(im['b64']));b[0]=255
            im['b64']=base64.b64encode(b).decode();im['sha256']=hashlib.sha256(b).hexdigest()
        elif name=='full_evidence_omitted':q['warm']['request']['full']=None
        elif name=='scorer_role_laundered':q['warm']['request']['full']['role']='scorer_only'
        elif name=='boolean_byte_count':r['cold']['request']['full']['nbytes']=True
        elif name=='actor_exit_missing':del r['actor_process']['exit']
        elif name=='unexpected_xvfb_stderr':rr[stable]['stderr']['xvfb.stderr']+='UNEXPECTED FAILURE\\n'
        else:raise ValueError(name)
    names=('missing_case','duplicate_case','wrong_point','stale_binding','authority_grant',
           'missing_release','held_button','missing_effect','source_identity','scorer_pixel_rehashed',
           'full_evidence_omitted','scorer_role_laundered','boolean_byte_count','actor_exit_missing',
           'unexpected_xvfb_stderr')
    baseline=analyze(records,construction,sources)
    rows=[]
    for name in names:
        copied=copy.deepcopy(records)
        before=json.dumps(copied,sort_keys=True)
        mutate(name,copied)
        changed=before!=json.dumps(copied,sort_keys=True)
        answer=analyze(copied,construction,sources)
        rows.append({'name':name,'changed':changed,'rejected':answer['status']=='REJECT',
                     'errors':answer['errors'][:8],'error_count':len(answer['errors'])})
    return {'status':'PASS' if baseline['status']=='PASS' and all(x['changed'] and x['rejected'] for x in rows) else 'REJECT',
            'baseline_status':baseline['status'],'controls':rows,'rejected':sum(r['rejected'] for r in rows),'count':len(rows)}

if __name__=='__main__':
    root=Path(sys.argv[1]);construction='--construction' in sys.argv
    output=Path(sys.argv[sys.argv.index('--output')+1]) if '--output' in sys.argv else None
    freeze=Path(__file__).with_name('FREEZE.json')
    sources=None if construction else json.loads(freeze.read_text())['sources']
    ans=run(load(root),construction,sources)
    rendered=json.dumps(ans,sort_keys=True,indent=2)+'\n'
    if output is not None:
        with output.open('x',encoding='utf-8') as f:f.write(rendered);f.flush()
    print(rendered,end='')
    raise SystemExit(0 if ans['status']=='PASS' else 1)
