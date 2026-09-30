"""Read-only checks of retained portable relay integration evidence."""
import base64,hashlib,io,json,tarfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def require(ok,message):
 if not ok:raise ValueError(message)
def main():
 manifest=json.loads((ROOT/'manifest.json').read_text())
 with tarfile.open(ROOT/'raw.tar.gz') as t:files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
 require(set(files)==set(manifest),'archive members')
 for n,b in files.items():require(len(b)==manifest[n]['bytes'] and hashlib.sha256(b).hexdigest()==manifest[n]['sha256'],n)
 def read(n):return json.loads(files[n])
 p='raw/portable-relay-primary-05/'
 def view(i):return json.loads(next(c['text'] for c in read(p+f'host/reply-{i}.json')['result']['content'] if c['type']=='text'))
 require([read(p+f'host/request-{i}.json')['tool'] for i in range(1,6)]==['interface_observe']+['interface_dispatch']*3+['interface_close'],'call order')
 targets=read(p+'targets.json')
 for i in [2,3,4]:
  v=view(i);require(v['outcome_summary']['execution_status']=='completed' and v['outcome_summary']['input_release_verified'] is True,'completed/released')
  require(v['session']['binding_revision']==1 and v['session']['targets']==targets,'no implicit rebind')
  ctx=v['post_dispatch_inspection'];e=ctx['evidence']
  require(ctx['target']=='left' and e['family_root']==targets['left'] and e['configured_target_path']==[targets['left'],e['managed_family_root']],'child ancestry')
  require(ctx['input_dispatched'] is False and ctx['authority_granted'] is False,'inspection has no input authority')
  require(ctx==read(p+'mcp/'+v['call_id']+'/report.json')['post_dispatch_inspection'],'full inspection equality')
 for i in [1,2,3,4]:
  raw=files[p+f'host/reply-{i}.json'];reply=json.loads(raw);review=read(p+f'host/review-{i}.json')
  require(review['reply_sha256']==hashlib.sha256(raw).hexdigest(),'review hash')
  imgs=[hashlib.sha256(base64.b64decode(c['data'],validate=True)).hexdigest() for c in reply['result']['content'] if c['type']=='image']
  require(imgs==[x['sha256'] for x in review['images']] and len(imgs)==1,'review image')
 require(view(5)['status']=='closed' and view(5)['release']['verified'] is True,'explicit close')
 events=[json.loads(x) for x in files[p+'host/host-events.jsonl'].decode().splitlines()]
 require(events[-1]['kind']=='transport_closed' and events[-1]['code']==0,'terminal transport')
 require(read(p+'left-effect.json')=={'saved':True,'text':'http://a_b'} and read(p+'evaluation.json')['success'] is True,'saved effect')
 require(p+'right-effect.json' not in files and p+'right-events.jsonl' not in files,'right untouched')
 audit=[json.loads(x) for x in files[p+'left-events.jsonl'].decode().splitlines()]
 require(''.join(x['char'] for x in audit if x.get('bindtag')=='AgentInterfacePassiveAudit' and x.get('char') and x['char'].isprintable())=='http://a_b','exact typed text')
 require(all(x['returncode'] is not None for x in read(p+'cleanup.json')),'fixture terminal')
 q='raw/portable-relay-primary-04/'
 refusal=json.loads(next(c['text'] for c in read(q+'host/reply-3.json')['result']['content'] if c['type']=='text'))['outcome_summary']
 require(refusal['execution_status']=='refused' and refusal['program_execution_started'] is False and refusal['program_emissions']==0,'retained refusal')
 require(read(q+'evaluation.json')['success'] is False and read(q+'host-reconciliation.json')['task_success'] is False,'retained host failure')
 require('raw/portable-relay-primary-01/failure.json' in files and 'raw/portable-relay-primary-02/failure.json' in files and 'raw/portable-relay-primary-03/interruption.json' in files,'retained interruptions/setup failure')
 b='raw/portable-relay-build-01/';bm=read(b+'manifest.json')
 require(hashlib.sha256(files[b+'runtime.pyz']).hexdigest()==bm['sha256'],'portable archive hash')
 with zipfile.ZipFile(io.BytesIO(files[b+'runtime.pyz'])) as z:
  require('runtime/cli_v1/mcp_relay.py' in z.namelist() and not any(n.startswith('research/') for n in z.namelist()),'packaged public relay without research')
 n='raw/portable-relay-native-01/';result=read(n+'result.json');require(result['status']=='PASS','native result')
 for suite in result['suites']:
  require(suite['returncode']==0,'suite returncode')
  for log in suite['logs'].values():require(hashlib.sha256(files[n+log['file']]).hexdigest()==log['sha256'],'native log hash')
 print(json.dumps({'status':'PASS','files':len(files),'scope':'retained evidence checks; not pixel interpretation or performance comparison'}))
if __name__=='__main__':main()
