"""Ten fixed mutations of retained local records; never re-executes encoders."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile
import zlib
from audit import audit, unpack

def pack(b):
    return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'zlib_b64':base64.b64encode(zlib.compress(b,9)).decode()}

def run(root):
    root=Path(root)
    original=audit(root)
    if not original['integrity_ok']:
        raise ValueError('baseline audit must pass')
    rows=[]
    for name in ['missing_condition','missing_sample','changed_input','changed_wire_sequence','negative_clock','missing_exit','wrong_sequence','wrong_dirty_count','wrong_arm_order','incomplete_batch']:
        with tempfile.TemporaryDirectory(prefix='d8c2-control-') as t:
            target=Path(t)/'study'
            shutil.copytree(root,target,ignore=shutil.ignore_patterns('.git','__pycache__'))
            assert audit(target)==original
            p=target/'raw'/'batch0.json'
            raw=json.loads(p.read_text()); row=raw['conditions'][0]; sample=row['samples'][0]['arms']['canonical']
            if name=='missing_condition': raw['conditions'].pop()
            elif name=='missing_sample': row['samples'].pop()
            elif name=='changed_input':
                b=bytearray(unpack(row['after']));b[0]^=1;row['after']=pack(bytes(b))
            elif name=='changed_wire_sequence':
                wire=unpack(row['packets']['canonical']['update']);n=struct.unpack('!I',wire[4:8])[0]
                meta=json.loads(wire[8:8+n]);meta['sequence']=3
                header=json.dumps(meta,separators=(',',':'),sort_keys=True).encode()
                wire=struct.pack('!4sI',b'AIT1',len(header))+header+wire[8+n:]
                row['packets']['canonical']['update']=pack(wire)
                for s in row['samples']+row['warmups']: s['arms']['canonical']['update_sha256']=hashlib.sha256(wire).hexdigest()
            elif name=='negative_clock': sample['wall_end']=sample['wall_start']-1
            elif name=='missing_exit':
                q=target/'raw'/'batch0.process.json'; r=json.loads(q.read_text());r['returncode']=None;q.write_text(json.dumps(r))
            elif name=='wrong_sequence': sample['sequence']=3
            elif name=='wrong_dirty_count': sample['changed_tiles']+=1
            elif name=='wrong_arm_order': row['samples'][0]['order'].reverse()
            elif name=='incomplete_batch': raw['complete']=False
            before=hashlib.sha256(p.read_bytes()).hexdigest()
            p.write_text(json.dumps(raw,separators=(',',':'))+'\n')
            after=hashlib.sha256(p.read_bytes()).hexdigest()
            result=audit(target)
            rows.append(dict(name=name,effective=(before!=after or name=='missing_exit'),rejected=not result['integrity_ok'],errors=result['errors']))
    return dict(baseline_disposition=original['disposition'],controls=rows,
                passed=all(x['effective'] and x['rejected'] for x in rows),count=len(rows))

if __name__=='__main__':
    import sys
    result=run(Path(__file__).resolve().parent)
    print(json.dumps(result,sort_keys=True,indent=2))
    raise SystemExit(0 if result['passed'] else 1)
