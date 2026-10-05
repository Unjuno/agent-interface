import hashlib,json,pathlib,subprocess,time
from model_client import ground,wait_path,P,CLI
R=pathlib.Path(__file__).resolve().parent;O=R/'runs/measured_consensus14'
if O.exists():raise RuntimeError('fresh allocation path required')
if hashlib.sha256(pathlib.Path(CLI).read_bytes()).hexdigest()!=P['cli_sha256']:raise RuntimeError('CLI drift')
for relative,digest in P['source_hashes'].items():
    if hashlib.sha256((R/relative).read_bytes()).hexdigest()!=digest:raise RuntimeError('source drift '+relative)
f=(R/'CLIENT_FIRST.txt').open('wb');native=subprocess.Popen(['pwsh','-NoProfile','-File',str(R/'run_once.ps1'),'-Phase','construction'],stdout=f,stderr=subprocess.STDOUT)
record={'native_launcher_pid':native.pid,'errors':[]}
try:
    ready=wait_path(O/'READY.json',native,30)['observation']
    adapted={'image':ready['native'],'source_sequence':ready['sequence']}
    proposal,summary=ground(O,'batch',adapted,{'a':17,'b':23},native);record.update(proposal=proposal,model_summary=summary)
finally:
    try:record['native_exit']=native.wait(170)
    except subprocess.TimeoutExpired:record['native_exit']='UNKNOWN';raise
    f.close();(R/'CLIENT_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
