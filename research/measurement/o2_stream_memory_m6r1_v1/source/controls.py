"""Effective corruption checks against copies; never execute the measurement."""
from pathlib import Path
import hashlib,json,shutil,sys,tempfile
from audit import audit

def run(root):
    root=Path(root);base=audit(root)
    if base['errors']:raise ValueError('baseline audit incomplete')
    changes=[('row_count',lambda r:r['samples'].pop()),
      ('sample_order',lambda r:r['samples'].reverse()),
      ('wall_delta',lambda r:r['samples'][4].__setitem__('wall_ns',r['samples'][4]['wall_ns']+100)),
      ('peak_delta',lambda r:r['samples'][-1]['memory'].__setitem__('increment',1)),
      ('state',lambda r:r['samples'][0]['state'].__setitem__('sequence',3)),
      ('wire_digest',lambda r:r['samples'][0].__setitem__('wire_sha256','0'*64)),
      ('affinity',lambda r:r.__setitem__('affinity',[-1])),
      ('freeze_identity',lambda r:r.__setitem__('freeze_sha256','0'*64))]
    results=[]
    for name,change in changes:
        with tempfile.TemporaryDirectory(prefix='m6r1-control-') as td:
            dest=Path(td)/'review';shutil.copytree(root,dest,ignore=shutil.ignore_patterns('construction','review-*','__pycache__'))
            path=dest/'formal/00/record.json';before=path.read_bytes();r=json.loads(before);change(r)
            path.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');after=path.read_bytes()
            assert before!=after
            value=audit(dest)
            if not value['errors']:raise AssertionError('ineffective control '+name)
            results.append(dict(name=name,rejected=True,errors=value['errors'],before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest()))
    for name,relative in [('source','source/stream_encoder.py'),('receipt','receipts/00.json')]:
        with tempfile.TemporaryDirectory(prefix='m6r1-control-') as td:
            dest=Path(td)/'review';shutil.copytree(root,dest,ignore=shutil.ignore_patterns('construction','review-*','__pycache__'))
            path=dest/relative;before=path.read_bytes()
            if name=='source':path.write_bytes(before+b'\n# retained-copy mutation\n')
            else:
                v=json.loads(before);v['returncode']=17;path.write_text(json.dumps(v))
            after=path.read_bytes();assert before!=after;value=audit(dest)
            if not value['errors']:raise AssertionError('ineffective control '+name)
            results.append(dict(name=name,rejected=True,errors=value['errors'],before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest()))
    return dict(rejected=len(results),total=10,controls=results,baseline_decision=base['decision'])

if __name__=='__main__':
    result=run(sys.argv[1]);text=json.dumps(result,sort_keys=True,indent=2)+'\n'
    if len(sys.argv)>2:Path(sys.argv[2]).write_text(text)
    else:print(text,end='')
