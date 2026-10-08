import hashlib,json,sys,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent;repo=root.parents[2];sys.path.insert(0,str(repo))
from runtime.cli_v1.public_presentation import brief_public_report
def require(ok,msg):
 if not ok:raise ValueError(msg)
m=json.loads((root/'manifest.json').read_text())
require(hashlib.sha256((root/'raw.tar.gz').read_bytes()).hexdigest()==m['archive_sha256'],'archive hash')
require(hashlib.sha256((repo/'runtime/cli_v1/public_presentation.py').read_bytes()).hexdigest()==m['projection_sha256'],'projection source changed')
with tarfile.open(root/'raw.tar.gz') as t:
 members=t.getmembers();require(len(members)==len(m['files']),'count')
 data={}
 for member in members:
  require(member.isfile() and member.name in m['files'],'unexpected member')
  value=t.extractfile(member).read()
  require(hashlib.sha256(value).hexdigest()==m['files'][member.name],'file hash')
  data[member.name]=value
 def obj(name):return json.loads(data[name])
 def view(i):
  r=obj('primary/host/reply-'+str(i)+'.json')
  return json.loads(next(c['text'] for c in r['result']['content'] if c['type']=='text'))
 size=lambda v:len(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
 for row in obj('primary/result.json')['rows']:
  i=row['attempt'];full=obj('primary/full-view-'+str(i)+'.json');live=view(i)
  require(brief_public_report(full)==live,'live projection')
  require(size(full)==row['full_bytes'] and size(live)==row['brief_bytes'],'size')
 require(view(3)['receipt']['source']['raw_report']==obj('primary/full-view-2.json')['receipt']['source']['raw_report'],'full retrieval')
 require(view(3)['operation_invoked'] is False,'retrieval side effect flag')
 refused=view(5)
 require(refused['outcome_summary']['execution_status']=='refused','refusal')
 require(refused['outcome_summary']['program_emissions']==0,'refused program input')
 require('raw_report' in refused['receipt']['source'],'failure truncated')
 require(obj('primary/effect.json')=={'saved':True,'text':'http://u_v'},'final saved effect')
 require(obj('primary/evaluation.json')['success'] is True,'evaluation')
 for i in (1,2,4,6):require('primary/host/review-'+str(i)+'.json' in data,'review missing')
 require(all(p['returncode'] is not None for p in obj('primary/cleanup.json')),'cleanup incomplete')
 print(json.dumps({'status':'PASS','files':len(data),'scope':'byte integrity, exact live projection/full retrieval, refusal and final saved effect; not latency or model quality proof'}))
