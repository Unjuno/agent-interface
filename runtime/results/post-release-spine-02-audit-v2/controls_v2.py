import hashlib,io,json,shutil,tarfile,tempfile
from pathlib import Path
from verify_v2 import verify
from analyze import analyze
p=Path(__file__).resolve().parent.parent/'post-release-spine-02';results={}
def reject(name,fn):
 try:fn()
 except Exception as e:results[name]={'rejected':True,'error':type(e).__name__+': '+str(e)}
 else:raise ValueError('control accepted '+name)
with tempfile.TemporaryDirectory() as td:
 root=Path(td);dest=root/'published';shutil.copytree(p,dest)
 b=(dest/'raw.tar.gz').read_bytes();(dest/'raw.tar.gz').write_bytes(b[:-1]+bytes([b[-1]^1]));reject('archive_corruption',lambda:verify(dest));(dest/'raw.tar.gz').write_bytes(b)
 with tarfile.open(p/'raw.tar.gz','r:gz') as t:
  for m in t.getmembers():
   file=root/'raw'/m.name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(t.extractfile(m).read())
 raw=root/'raw/post-release-spine-02'
 for name,file,change in [
  ('wrong_independent_score',raw/'direct-post/session/evaluation-at-close.json',lambda v:v.update(success=False)),
  ('wrong_review_image',raw/'direct-post/host/review-8.json',lambda v:v['images'][0].update(sha256='0'*64)),
  ('refusal_emitted_input',raw/'guarded-local/host/reply-14.json',None)]:
  original=file.read_bytes();v=json.loads(original)
  if change:change(v)
  else:
   block=next(x for x in v['result']['content'] if x['type']=='text');m=json.loads(block['text']);m['result']['input_dispatched']=True;block['text']=json.dumps(m)
  file.write_text(json.dumps(v));eventfile=raw/'guarded-local/host/host-events.jsonl';eventoriginal=eventfile.read_bytes()
  if name=='refusal_emitted_input':
   digest=hashlib.sha256(file.read_bytes()).hexdigest();events=[json.loads(x) for x in eventoriginal.splitlines()];
   for event in events:
    if event.get('attempt')==14 and 'reply_sha256' in event:event['reply_sha256']=digest
   eventfile.write_text(''.join(json.dumps(x)+'\n' for x in events))
  reject(name,lambda:analyze(raw));file.write_bytes(original);eventfile.write_bytes(eventoriginal)
 members=[]
 with tarfile.open(p/'raw.tar.gz','r:gz') as t:
  members=[(m,t.extractfile(m).read()) for m in t.getmembers()]
 with tarfile.open(dest/'raw.tar.gz','w:gz') as t:
  for m,content in members[1:]:t.addfile(m,io.BytesIO(content))
 v=json.loads((dest/'manifest.json').read_text());b=(dest/'raw.tar.gz').read_bytes();v['archive']={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};(dest/'manifest.json').write_text(json.dumps(v));reject('missing_member',lambda:verify(dest))
print(json.dumps(results,indent=2))
