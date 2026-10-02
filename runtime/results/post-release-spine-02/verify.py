import argparse,hashlib,json,tarfile,tempfile
from pathlib import Path,PurePosixPath
from analyze import analyze,require,load

def verify(dest):
 manifest=load(dest/'manifest.json');data=(dest/'raw.tar.gz').read_bytes();require(len(data)==manifest['archive']['bytes'] and hashlib.sha256(data).hexdigest()==manifest['archive']['sha256'],'archive hash')
 expected={x['path']:x for x in manifest['files']};require(len(expected)==len(manifest['files']),'manifest duplicate')
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);seen=set()
  with tarfile.open(dest/'raw.tar.gz','r:gz') as t:
   for m in t.getmembers():
    p=PurePosixPath(m.name);require(m.isfile() and not p.is_absolute() and '..' not in p.parts and m.name in expected and m.name not in seen,'unsafe or duplicate archive path');seen.add(m.name)
    b=t.extractfile(m).read();row=expected[m.name];require(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'file hash '+m.name)
    out=root/m.name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
  require(seen==set(expected),'missing member')
  actual=analyze(root/'post-release-spine-02');require(actual==load(root/'post-release-spine-02/analysis-v3.json')==load(dest/'analysis.json'),'analysis mismatch')
  stop=root/'post-release-spine-01/guarded-local';require(load(stop/'session/finish.json')['status']=='STOP_CONSTRUCTION_NO_INPUT','retained STOP');o=load(stop/'session/evaluation-at-close.json');require(o['success'] is False and o['record_count']==0 and len(o['missing'])==6,'STOP six missing');require((stop/'host/host-events.jsonl').read_bytes()==b'','STOP no requests')
  usage=load(root/'post-release-spine-02/model-usage-projection.json');require(usage==load(dest/'model-usage-projection.json') and usage['dollars'] is None,'usage identity');require(all(x['local_context']['model']=='gpt-6.1-sol' and x['local_context']['effort']=='medium' for x in usage['calls'] if x['local_context']),'model labels')
  return {'status':actual['status'],'files':len(seen),'integration_gate':actual['integration_gate'],'scope':'Retained effect/history, neutral releases, exact image/review identity, source archive identity, all attempts and attributed timing. No autonomous recovery or independent perception/cost proof.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();print(json.dumps(verify(a.directory)))
