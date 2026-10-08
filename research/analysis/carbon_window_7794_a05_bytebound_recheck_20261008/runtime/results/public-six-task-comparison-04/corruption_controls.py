import pathlib,tempfile,tarfile,io,json,hashlib,subprocess,shutil
root=pathlib.Path(__file__).resolve().parent
original=(root/'raw.tar.gz').read_bytes()
with tarfile.open(fileobj=io.BytesIO(original),mode='r:gz') as t:raw={m.name:t.extractfile(m).read() for m in t.getmembers()}
def change_release(data):
 q='current/direct/host/reply-3.json';r=json.loads(data[q]);m=json.loads(r['result']['content'][0]['text']);m['receipt']['source']['raw_report']['result']['execution']['releases'][0]['verified']=False;r['result']['content'][0]['text']=json.dumps(m);data[q]=json.dumps(r).encode()
def change_effect(data):
 q='current/guarded/submission-history.jsonl';lines=data[q].splitlines();r=json.loads(lines[0]);r['submitted_values']=['wrong-token'];lines[0]=json.dumps(r).encode();data[q]=b'\n'.join(lines)+b'\n'
records=[]
for name,mutator,expected in [('unverified-release',change_release,'input releases'),('wrong-independent-effect',change_effect,'exact token/layout')]:
 data=dict(raw);mutator(data)
 with tempfile.TemporaryDirectory(prefix='public04-readonly-control-') as temp:
  p=pathlib.Path(temp);shutil.copyfile(root/'verify.py',p/'verify.py')
  with tarfile.open(p/'raw.tar.gz','w:gz') as t:
   for n,b in data.items():i=tarfile.TarInfo(n);i.size=len(b);t.addfile(i,io.BytesIO(b))
  m={'archive_sha256':hashlib.sha256((p/'raw.tar.gz').read_bytes()).hexdigest(),'files':[{'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in data.items()]};(p/'manifest.json').write_text(json.dumps(m))
  r=subprocess.run(['python3','-O',str(p/'verify.py')],capture_output=True,text=True);ok=r.returncode!=0 and expected in r.stderr
  records.append({'control':name,'rehash_all_members':True,'exit':r.returncode,'rejected_for_expected_reason':ok,'error_tail':r.stderr.splitlines()[-1]})
  if not ok:raise ValueError(records[-1])
result=subprocess.run(['python3','-O',str(root/'verify.py')],capture_output=True,text=True);(root/'audit.json').write_text(result.stdout);(root/'audit-stderr.txt').write_text(result.stderr)
if result.returncode!=0:raise ValueError('original audit failed')
(root/'corruption-controls.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))
