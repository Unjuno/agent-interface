"""Eight explicit saved-evidence corruptions; no GUI or runtime execution."""
import copy, json, shutil, sys, tempfile
from pathlib import Path
from audit import audit

def main(root):
    root=Path(root); rows=[]
    assert not audit(root)['errors']
    for name in ('missing_case','session','value','held_key','lock','failure_index','exit','import'):
        with tempfile.TemporaryDirectory(prefix='k8n4-control-') as temp:
            dst=Path(temp)/'copy';shutil.copytree(root,dst,ignore=shutil.ignore_patterns('controls-work'))
            assert not audit(dst)['errors']
            folder=dst/'formal/batch1/PROGRAM_ON';p=folder/'record.json';r=json.loads(p.read_text())
            if name=='missing_case': shutil.rmtree(folder)
            else:
                if name=='session': r['session']='wrong-session'
                elif name=='value': r['app_after']['value']='1aB2'
                elif name=='held_key': r['terminal']['keymap'][4]=1
                elif name=='lock': r['terminal']['lock']=False;r['terminal']['mask']=0
                elif name=='failure_index':
                    r['response']['result']['execution']['failed_op']=2
                    (folder/'response.json').write_text(json.dumps(r['response']))
                elif name=='exit': r['app']['exit']=7
                elif name=='import': r['runtime_imports']['runtime.cli_v1.api']['sha256']='0'*64
                p.write_text(json.dumps(r))
            result=audit(dst);rows.append({'mutation':name,'detected':bool(result['errors']),'errors':result['errors']})
    print(json.dumps({'controls':rows,'detected':sum(x['detected'] for x in rows),'total':len(rows)},indent=2,sort_keys=True))
    return int(not all(x['detected'] for x in rows))
if __name__=='__main__':raise SystemExit(main(sys.argv[1]))
