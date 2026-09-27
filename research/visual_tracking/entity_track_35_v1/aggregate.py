#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path
import study

def main(root,out):
    root=Path(root); out=Path(out); out.mkdir(exist_ok=False); rows=[]; batch_receipts=[]
    for b in range(4):
        d=root/f'formal-02-batch-{b}'
        end=json.loads((d/'END.json').read_text()); batch_receipts.append(end)
        if end['returncode']!=0 or end['cases']!=12 or end['xvfb']['returncode']!=0: raise RuntimeError(('batch',b,end))
        for i in range(b*12,(b+1)*12):
            src=d/f'case-{i:02d}.json'; dst=out/src.name; shutil.copyfile(src,dst); rows.append(json.loads(src.read_text()))
    if [r['index'] for r in rows]!=list(range(48)): raise RuntimeError('index denominator')
    result=study.summarize(rows); (out/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    (out/'END.json').write_text(json.dumps({'returncode':0,'cases':48,'batches':batch_receipts,'xvfb':{'returncode':0}},sort_keys=True)+'\n')
    return 0
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('aggregate.py ROOT OUT')
    raise SystemExit(main(sys.argv[1],sys.argv[2]))
