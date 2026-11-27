"""Verify and replay the sealed, bounded MAP01 state alignment audit."""
import hashlib,json,pathlib,subprocess,sys,tempfile,zipfile
P=pathlib.Path(__file__).resolve().parent
ARCHIVE='85f43069c7656a8738a3fe729c0d724fb749bc0d18548c443533b1ff707a7deb'
SEAL='a6dcaeafed7ef09fb855cc6e7228cd869aef8b4fcffe95a3039c7bd114ecde59'
def digest(b):return hashlib.sha256(b).hexdigest()
def require(x,m):
 if not x:raise ValueError(m)
require(digest((P/'evidence.zip').read_bytes())==ARCHIVE,'archive digest differs')
with zipfile.ZipFile(P/'evidence.zip') as z, tempfile.TemporaryDirectory() as td:
 names=z.namelist();require(len(names)==len(set(names)),'duplicate member')
 require(digest(z.read('seal.json'))==SEAL,'seal differs');rows=json.loads(z.read('seal.json'))['files'];entries={r['path']:r for r in rows}
 require(len(entries)==len(rows) and set(names)==set(entries)|{'seal.json'},'inventory differs')
 root=pathlib.Path(td)
 for name in names:
  part=pathlib.PurePosixPath(name);require(not part.is_absolute() and all(x not in ('..','.') for x in part.parts) and '\\' not in name,'unsafe path')
  data=z.read(name)
  if name!='seal.json':
   row=entries[name];require(len(data)==row['bytes'] and digest(data)==row['sha256'],'entry differs')
  target=root.joinpath(*part.parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 expected=json.loads((root/'report.json').read_text(encoding='utf-8-sig'))
 for flags in ([],['-O']):
  run=subprocess.run([sys.executable,*flags,str(root/'audit.py')],capture_output=True,text=True,check=True)
  require(json.loads(run.stdout)==expected,'replay differs')
 print(json.dumps({'status':'audited','trials':len(expected['trials']),'scope':'retrospective evidence; no new game execution'},sort_keys=True))
