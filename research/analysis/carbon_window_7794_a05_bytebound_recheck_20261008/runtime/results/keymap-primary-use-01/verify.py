import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
def require(condition,message):
 if not condition:raise ValueError(message)
require(hashlib.sha256((root/'raw.tar.gz').read_bytes()).hexdigest()==manifest['archive_sha256'],'archive hash')
with tarfile.open(root/'raw.tar.gz') as t:
 members=t.getmembers()
 require(len(members)==len(manifest['files']),'file count')
 require({m.name for m in members}==set(manifest['files']),'file set')
 data={}
 for m in members:
  require(m.isfile(),'nonregular member')
  b=t.extractfile(m).read();expected=manifest['files'][m.name]
  require(len(b)==expected['bytes'] and hashlib.sha256(b).hexdigest()==expected['sha256'],'file integrity: '+m.name)
  data[m.name]=b
 effect=json.loads(data['primary/effect.json'])
 require(effect=={'saved':True,'text':'http://c_d'},'final saved effect')
 require(json.loads(data['primary/evaluation.json'])['success'] is True,'evaluation')
 for i in (1,2,3):
  require('primary/host/review-'+str(i)+'.json' in data,'caller review receipt')
 for i,tool in enumerate(('interface_observe','interface_dispatch','interface_dispatch','interface_close'),1):
  require(json.loads(data['primary/host/request-'+str(i)+'.json'])['tool']==tool,'call sequence')
 require(json.loads(data['primary/host-timing.json'])['timeline_status']=='complete','timeline')
 require(all(p['returncode'] is not None for p in json.loads(data['primary/cleanup.json'])),'cleanup')
print(json.dumps({'status':'PASS','files':len(data),'scope':'retained byte integrity, call sequence, final saved effect and completed cleanup; no visual/latency inference'}))
