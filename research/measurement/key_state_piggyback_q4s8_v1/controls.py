"""Effective, well-formed copied-evidence mutations; never starts an X process."""
from pathlib import Path
import copy,json,shutil,sys,tempfile
import audit

def run(root,formal=True):
    root=Path(root);baseline=audit.evaluate(root,formal)
    if baseline['errors']:raise ValueError('intact baseline must pass')
    results=[]
    for name in ('decision','request','focus','event','exit','clock','authority','denominator','writer','witness'):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'copy';shutil.copytree(root,target)
            if audit.evaluate(target,formal)['errors']:raise ValueError('intact relocated copy failed')
            path=target/'DOWN/block-00.json';raw=json.loads(path.read_bytes());before=copy.deepcopy(raw)
            if name=='decision':raw['samples'][2]['state']['decision']['shift_down']=False
            elif name=='request':raw['samples'][2]['focus']['r1']+=1
            elif name=='focus':raw['samples'][2]['focus']['focus']+=1
            elif name=='event':raw['samples'][2]['state']['events'][0]['keycode']+=1
            elif name=='exit':
                path=target/'DOWN/writer.process.json';raw=json.loads(path.read_bytes());before=copy.deepcopy(raw);raw['returncode']=True
            elif name=='clock':raw['samples'][2]['end_ns']=raw['samples'][2]['start_ns']-1
            elif name=='authority':raw['samples'][2]['authority']='execute'
            elif name=='denominator':raw['samples'].pop()
            elif name=='writer':raw['mutation']['result']['operations'][0]['down']=False
            elif name=='witness':raw['before']['result']['keymap']='00'*32
            if raw==before:raise ValueError('no-op control '+name)
            path.write_text(json.dumps(raw,sort_keys=True)+'\n')
            result=audit.evaluate(target,formal)
            if not result['errors']:raise ValueError('undetected control '+name)
            results.append(dict(name=name,intact_pass=True,changed=True,rejected=True,errors=len(result['errors'])))
    return dict(status='PASS_EFFECTIVE_CONTROLS',controls=results,count=len(results))
if __name__=='__main__':print(json.dumps(run(sys.argv[1],len(sys.argv)<3 or sys.argv[2]!='construct'),sort_keys=True,indent=2))
