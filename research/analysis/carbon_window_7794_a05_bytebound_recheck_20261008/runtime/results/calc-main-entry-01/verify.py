import base64,hashlib,io,json,sys,tarfile,zipfile
from pathlib import Path
import openpyxl
def require(value,message):
 if not value:raise ValueError(message)
def sha(value):return hashlib.sha256(value).hexdigest()
def audit(files):
 def read(name):return json.loads(files[name])
 source='443bcb63333c4614d9a6fee5cb3ca3f9f6ea9710'
 results=[]
 for suffix,count in [('01',7),('02',12)]:
  root='calc-main-entry-'+suffix;host=root+'/host';session=root+'/session'
  plan=read(root+'/PLAN.json');require(plan['source']==source,'source')
  for name,digest in plan['hashes'].items():require(sha(files[root+'/'+name])==digest,'frozen '+name)
  with zipfile.ZipFile(io.BytesIO(files[root+'/runtime.pyz'])) as z:
   build=json.loads(z.read('BUILD.json'));require(build['source_revision']==source,'portable source')
   for entry in build['source_files']:require(sha(z.read(entry['path']))==entry['sha256'],'portable module')
  require(sum(n.startswith(host+'/request-') and n.endswith('.json') for n in files)==count,'request inventory')
  events=[json.loads(l) for l in files[host+'/host-events.jsonl'].decode().splitlines()]
  require([e['sequence'] for e in events]==list(range(1,len(events)+1)),'event sequence')
  replies=[];requests=[];rows=[];images=0
  for i in range(1,count+1):
   request=read(host+f'/request-{i}.json');reply=read(host+f'/reply-{i}.json');requests.append(request);replies.append(reply)
   require(request['id']==reply['id']==i and reply['status']=='returned','response identity')
   relevant=[e for e in events if e.get('attempt')==i];kinds=[e['kind'] for e in relevant]
   require(kinds[:4]==['send_requested','reply_available','presentation_started','presentation_callbacks_completed'],'presentation order')
   digest=sha(files[host+f'/reply-{i}.json'])
   require(all(e.get('reply_sha256',digest)==digest for e in relevant),'response digest')
   content=reply['result']['content'];pictures=[c for c in content if c['type']=='image'];images+=len(pictures)
   if pictures:
    require(kinds[-1]=='review_recorded' and host+f'/review-{i}.json' in files,'image review')
   else:require(kinds[-1]=='text_acknowledgment_recorded','text acknowledgement')
   if reply['result'].get('isError'):
    require(suffix=='01' and request['tool']=='interface_dispatch' and 'inspect_after' in content[0]['text'],'preserved caller error')
    rows.append(None);continue
   row=json.loads(next(c['text'] for c in content if c['type']=='text'));rows.append(row)
   if 'call_id' in row:
    report=read(session+'/server/'+row['call_id']+'/report.json')
    for picture in pictures:
     png=base64.b64decode(picture['data'],validate=True)
     require(any(sha(b)==sha(png) for n,b in files.items() if n.startswith(session+'/server/'+row['call_id']+'/images/') and n.endswith('.png')),'original retained PNG')
    if request['tool']=='interface_dispatch':
     require(report['result']['status']=='completed' and report['result']['admission']=='accepted','completed input')
     releases=report['result']['execution']['releases']
     require(releases and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'neutral input')
     require(report['post_dispatch_inspection']['input_dispatched'] is False,'read-only post inspection')
  require(requests[-1]['tool']=='interface_close' and rows[-1]['status']=='closed','public close')
  require(read(host+'/exit.json')=={'code':0,'signal':None},'transport terminal')
  require(all(type(p['returncode']) is int for p in read(session+'/cleanup.json')),'owned terminal')
  book=openpyxl.load_workbook(io.BytesIO(files[session+'/saved.xlsx']),data_only=True)
  actual={'A1':book.active['A1'].value,'A2':book.active['A2'].value};effect=read(session+'/independent-effect.json')
  require(actual==effect['actual'],'independent workbook consistency')
  if suffix=='01':
   require(actual=={'A1':None,'A2':None} and effect['passed'] is False,'failed trial preserved')
   require([r['tool'] for r in requests]==['interface_observe','interface_inspect_target','interface_review_target','interface_observe','interface_clock','interface_dispatch','interface_close'],'failure call order')
   require(rows[5] is None and read(session+'/finish.json')['status']=='STOP_CALLER_SCHEMA_ERROR','first failure STOP')
  else:
   require(actual=={'A1':731,'A2':864} and effect['passed'] is True,'exact saved values')
   require([r['tool'] for r in requests]==['interface_inspect_target','interface_review_target','interface_clock','interface_dispatch','interface_review_target','interface_clock','interface_dispatch','interface_review_target','interface_clock','interface_dispatch','interface_inspect_target','interface_close'],'successful call order')
   require(all(r['result']['isError'] is False for r in replies),'no tool errors')
   require([rows[i]['binding_revision'] for i in [1,4,7]]==[2,3,4],'explicit modal binding revisions')
   require(read(session+'/finish.json')['extra_disk_previews']==0,'no disk preview')
  send=[e for e in events if e['kind']=='send_requested'];last=next(e for e in events if e['kind']=='transport_closed')
  results.append({'trial':suffix,'calls':count,'images':images,'saved':actual,'host_interval_ms':last['host_monotonic_ms']-send[0]['host_monotonic_ms'],'child_returncodes':[p['returncode'] for p in read(session+'/cleanup.json')]})
 return {'source':source,'trials':results,'scope':'Scoped real Calc primary use, one stopped caller error and one correct saved workbook. No speed, isolated semantic latency, token/cost or general desktop claim.'}
def verify(directory):
 root=Path(directory);manifest=json.loads((root/'raw-manifest.json').read_text());files={}
 with tarfile.open(root/'raw.tar.gz','r:gz') as archive:
  for member in archive.getmembers():
   require(member.isfile() and member.name not in files,'unique regular archive member')
   files[member.name]=archive.extractfile(member).read()
 require(set(files)==set(manifest),'manifest inventory')
 for name,data in files.items():require(len(data)==manifest[name]['bytes'] and sha(data)==manifest[name]['sha256'],'manifest bytes '+name)
 result=audit(files);print(json.dumps(result,indent=2));return result
if __name__=='__main__':verify(Path(__file__).resolve().parent)
