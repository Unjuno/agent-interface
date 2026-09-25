"""Effective well-formed copied-evidence mutations; never starts GUI workers."""
import copy,hashlib,json,shutil,sys,tempfile
from pathlib import Path
import audit

def controls(root,phase):
    base=audit.run(root,phase)
    if base['errors']:raise RuntimeError('BASELINE_AUDIT_FAILED')
    result=[]
    for kind in ['first_offset','missing_case','case_id','motion','neutral','process_exit','svg_geometry','image_hash']:
        with tempfile.TemporaryDirectory(prefix='f2a6-audit-') as t:
            dst=Path(t)/'copy';shutil.copytree(root,dst,ignore=shutil.ignore_patterns('__pycache__'))
            p=dst/'data'/phase/'case00'/'raw'/'CASE.json';r=json.loads(p.read_text());before=p.read_bytes()
            if kind=='missing_case':p.unlink()
            elif kind=='first_offset':r['spec']['first']=[99,99]
            elif kind=='case_id':r['spec']['id']='wrong-id'
            elif kind=='motion':
                e=next(e for e in r['events'] if e.get('role')=='task' and e['kind']=='motion');e['x']+=1
                (p.parent/'EVENTS.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in r['events']))
            elif kind=='neutral':r['final_motor']['keymap_hex']='01'+'00'*31
            elif kind=='process_exit':
                q=p.parent.parent/'PROCESS.json';z=json.loads(q.read_text());z['exit']=False;q.write_text(json.dumps(z))
            elif kind=='svg_geometry':
                q=p.parent/'after.svg';raw=q.read_bytes().replace(b'width="40"',b'width="42"');assert raw!=q.read_bytes();q.write_bytes(raw);r['after_sha256']=hashlib.sha256(raw).hexdigest()
            elif kind=='image_hash':
                e=next(e for e in r['events'] if e['kind']=='image');e['sha256']='0'*64
            if kind!='missing_case':p.write_text(json.dumps(r,sort_keys=True)+'\n')
            out=audit.run(dst,phase);ok=bool(out['errors'])
            result.append({'name':kind,'rejected':ok,'errors':out['errors']})
            if not ok:raise RuntimeError('UNDETECTED:'+kind)
    return {'controls':result,'rejected':len(result),'baseline_errors':base['errors']}
if __name__=='__main__':print(json.dumps(controls(Path(sys.argv[1]),sys.argv[2]),sort_keys=True,indent=2))
