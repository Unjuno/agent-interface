"""Effective copied-evidence challenges; no validation-program run is repeated."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from audit import audit


def controls(out: Path) -> dict:
    results=[]
    for kind in ('missing_row','wrong_exit','authority','task_success','wrong_hash',
                 'echo_payload','reversed_time','not_isolated','bad_launcher','changed_archive'):
        with tempfile.TemporaryDirectory() as tmp:
            copy=Path(tmp)/'copy';shutil.copytree(out,copy)
            if audit(copy)['errors']:raise RuntimeError('unmodified control baseline failed')
            raw=copy/'RAW.jsonl'; rows=[json.loads(x) for x in raw.read_text().splitlines()]
            if kind=='missing_row':rows.pop()
            elif kind=='wrong_exit':rows[0]['returncode']=99
            elif kind in ('authority','task_success','echo_payload'):
                report=json.loads(rows[0]['stdout'])
                if kind=='authority':report['side_effect_authority']=True
                elif kind=='task_success':report['task_success']=True
                else:report['detail']='PRIVATE_PAYLOAD_87'
                rows[0]['stdout']=json.dumps(report)+'\n'
            elif kind=='wrong_hash':rows[0]['input_after_sha256']='0'*64
            elif kind=='reversed_time':rows[0]['end_ns']=rows[0]['start_ns']-1
            elif kind=='not_isolated':rows[0]['argv'].remove('-I')
            elif kind=='bad_launcher':
                p=copy/'LAUNCHER.json';d=json.loads(p.read_text());d['returncode']=1;p.write_text(json.dumps(d))
            else:
                p=copy/'validator.pyz';p.write_bytes(p.read_bytes()+b'changed')
                p=copy/'artifact.json';d=json.loads(p.read_text());d['sha256']=hashlib.sha256((copy/'validator.pyz').read_bytes()).hexdigest();p.write_text(json.dumps(d))
            if kind not in ('bad_launcher','changed_archive'):
                raw.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
            response=audit(copy)
            results.append({'kind':kind,'rejected':bool(response['errors']),'errors':response['errors']})
    return {'controls':results,'all_rejected':all(x['rejected'] for x in results)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args()
    result=controls(a.out);print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(not result['all_rejected'])
