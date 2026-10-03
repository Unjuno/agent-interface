import copy, hashlib, importlib.util, json, shutil, sys
from pathlib import Path

here=Path(__file__).resolve().parent
auditor=Path(sys.argv[1]).resolve()
out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('raw_auditor',auditor);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
definitions=[('duplicate-dispatch','candidate/relay-received.jsonl','append first complete row'),('wrong-owner-exit','candidate/process.json','exit.code=0'),('missing-return','candidate/stdout.jsonl','remove returned row'),('wrong-relay-exit','candidate/host/exit.json','code=1'),('boolean-attempt','candidate/exchange/original-reply-1.json','attempt=true')]
reports=[]
for name,path,operation in definitions:
    root=out/name;shutil.copytree(here/'pipe',root)
    target=root/path;before=target.read_bytes()
    if name=='duplicate-dispatch': target.write_bytes(before+before)
    elif name=='missing-return':
        rows=[json.loads(row) for row in before.splitlines()];target.write_text(''.join(json.dumps(row)+'\n' for row in rows if row['status']!='returned'),encoding='utf-8',newline='\n')
    else:
        row=json.loads(before)
        if name=='wrong-owner-exit':row['exit']['code']=0
        elif name=='wrong-relay-exit':row['code']=1
        else:row['attempt']=True
        target.write_text(json.dumps(row)+'\n',encoding='utf-8',newline='\n')
    try: module.audit(root);outcome='FALSE_ACCEPT';reason=None
    except ValueError as error:outcome='REJECTED';reason=str(error)
    reports.append({'name':name,'path':path,'mutation':operation,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'outcome':outcome,'reason':reason})
report={'auditor_sha256':hashlib.sha256(auditor.read_bytes()).hexdigest(),'definitions':definitions,'controls':reports,'false_accepts':sum(x['outcome']=='FALSE_ACCEPT' for x in reports)}
(out/'controls.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report,sort_keys=True))
sys.exit(1 if report['false_accepts'] else 0)
