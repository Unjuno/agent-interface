"""Reproducible data-only audit mutations; never starts experiment actors."""
from __future__ import annotations
import argparse,copy,hashlib,json,shutil,tempfile
from pathlib import Path
from audit import audit

NAMES=['status','upper_bound','lower_open','authority','task_success','duplicate_id',
       'missing_row','input_calibration','infeasible_extremizer','nominal_status','source_identity','actual_exit']

def control(root:Path,data:Path,index:int):
    baseline=audit(root,data)
    if baseline['errors']:raise RuntimeError('intact baseline fails')
    original=(data/'raw.jsonl').read_bytes()
    rows=[json.loads(x) for x in original.splitlines()]
    pos=next(i for i,x in enumerate(rows) if 'interval' in x['output'])
    row=rows[pos];name=NAMES[index]
    with tempfile.TemporaryDirectory(prefix='c6t9-data-control-') as tmp:
        target=Path(tmp)/'data';shutil.copytree(data,target)
        changed_root=root
        before_extra=None;after_extra=None
        if name=='status':row['output']['status']='CORRUPTED'
        elif name=='upper_bound':row['output']['interval'][1]='999999'
        elif name=='lower_open':row['output']['lower_open']=False
        elif name=='authority':row['output']['grants_input_authority']=True
        elif name=='task_success':row['output']['task_success']=True
        elif name=='duplicate_id':rows[1]['id']=rows[0]['id']
        elif name=='missing_row':rows.pop()
        elif name=='input_calibration':row['input']['samples'][0]['hi']='999999'
        elif name=='infeasible_extremizer':row['output']['extremizers']['upper']=['-10','999']
        elif name=='nominal_status':row['output']['nominal']['status']='CORRUPTED'
        elif name=='source_identity':
            changed_root=Path(tmp)/'source-scope';changed_root.mkdir()
            freeze=json.loads((root/'FREEZE.json').read_text())
            for p in list(freeze['files'])+['FREEZE.json']:
                dst=changed_root/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/p,dst)
            p=changed_root/'source/clock_bounds.py'
            before_extra=hashlib.sha256(p.read_bytes()).hexdigest();p.write_bytes(p.read_bytes()+b'\n# mutated evidence\n')
            after_extra=hashlib.sha256(p.read_bytes()).hexdigest()
        elif name=='actual_exit':
            p=target/'launcher.json';before_extra=hashlib.sha256(p.read_bytes()).hexdigest()
            d=json.loads(p.read_text());d['exit_code']=23;p.write_text(json.dumps(d)+'\n')
            after_extra=hashlib.sha256(p.read_bytes()).hexdigest()
        if name not in {'source_identity','actual_exit'}:
            (target/'raw.jsonl').write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in rows))
        mutated=(target/'raw.jsonl').read_bytes()
        changed=mutated!=original or before_extra!=after_extra
        result=audit(changed_root,target)
        genuine=bool(result['errors']) and not any(x.startswith('EVIDENCE_UNREADABLE') for x in result['errors'])
        return {'name':name,'intact_baseline_passed':True,'mutation_effective':changed,
            'raw_before_sha256':hashlib.sha256(original).hexdigest(),
            'raw_after_sha256':hashlib.sha256(mutated).hexdigest(),
            'extra_before_sha256':before_extra,'extra_after_sha256':after_extra,
            'audit':result,'rejected_without_parser_exception':genuine,
            'pass':changed and genuine}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('data');ap.add_argument('index',type=int);args=ap.parse_args()
    if not 0<=args.index<len(NAMES):raise SystemExit('control index')
    r=control(Path(__file__).resolve().parent.parent,Path(args.data),args.index)
    print(json.dumps(r,sort_keys=True,indent=2));raise SystemExit(not r['pass'])
