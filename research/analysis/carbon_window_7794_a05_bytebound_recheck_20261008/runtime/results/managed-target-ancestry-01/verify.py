"""Read-only checks of the retained primary trial."""
import base64,hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def require(ok,message):
 if not ok:raise ValueError(message)
def main():
 manifest=json.loads((ROOT/'manifest.json').read_text())
 with tarfile.open(ROOT/'raw.tar.gz') as tar:
  files={m.name:tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
 require(set(files)==set(manifest),'members')
 for name,data in files.items():require(len(data)==manifest[name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[name]['sha256'],name)
 def read(name):return json.loads(files[name])
 def view(i):return json.loads(next(c['text'] for c in read(f'primary/host/reply-{i}.json')['result']['content'] if c['type']=='text'))
 tools=['observe','dispatch','review_target','dispatch','dispatch','dispatch','close']
 require([read(f'primary/host/request-{i}.json')['tool'] for i in range(1,8)]==['interface_'+x for x in tools],'calls')
 targets=read('primary/targets.json');first=view(2);context=first['post_dispatch_inspection'];evidence=context['evidence']
 require(first['session']['targets']==targets and first['session']['binding_revision']==1,'no implicit rebind')
 require(evidence['family_root']==targets['left'] and evidence['configured_target_path']==[targets['left'],evidence['managed_family_root']],'child ancestry')
 require(evidence['window_id']==evidence['managed_family_root'],'resolved window')
 selection=read('primary/host/request-3.json')['arguments']
 require(all(selection[k]==v for k,v in context['review_request']['arguments'].items()),'explicit candidate selection')
 require(view(3)['binding_revision']==2 and view(3)['previous_window_id']==targets['left'] and view(3)['window_id']==evidence['window_id'],'selection transition')
 require(view(3)['capture_consistency']=='matched','selection capture')
 for i in [2,5,6]:
  v=view(i);require(v['receipt']['schema']=='agent-interface/receipt-view-dispatch-summary-v1','summary')
  require(v['outcome_summary']['execution_status']=='completed' and v['outcome_summary']['input_release_verified'] is True,'completed and released')
  ctx=v['post_dispatch_inspection'];require(ctx['evidence']==evidence,'ancestry stable after review')
  report=read('primary/mcp/'+v['call_id']+'/report.json')
  require(ctx==report['post_dispatch_inspection'],'complete inspection retained')
  require(ctx['input_dispatched'] is False and ctx['authority_granted'] is False,'no inspection authority')
 refused=view(4)['outcome_summary']
 require(refused['execution_status']=='refused' and refused['program_execution_started'] is False and refused['program_emissions']==0,'invalid HOME no program emissions')
 require(view(4)['post_dispatch_inspection']['status']=='skipped','refusal skip')
 for i in [1,2,3,5,6]:
  raw=files[f'primary/host/reply-{i}.json'];reply=json.loads(raw);review=read(f'primary/host/review-{i}.json')
  require(review['reply_sha256']==hashlib.sha256(raw).hexdigest(),'review reply hash')
  images=[hashlib.sha256(base64.b64decode(c['data'],validate=True)).hexdigest() for c in reply['result']['content'] if c['type']=='image']
  require(images==[x['sha256'] for x in review['images']] and len(images)==1,'review image hash')
 require(read('primary/left-effect.json')=={'saved':True,'text':'http://m_n'},'saved effect')
 require(read('primary/evaluation.json')['success'] is True,'evaluation')
 require('primary/right-events.jsonl' not in files and 'primary/right-effect.json' not in files,'right untouched')
 rows=[json.loads(line) for line in files['primary/left-events.jsonl'].decode().splitlines()]
 audit=[r for r in rows if r.get('bindtag')=='AgentInterfacePassiveAudit']
 require(''.join(r['char'] for r in audit if r['char'] and r['char'].isprintable())=='ttp://m_nh','missing prefix and one h repair retained')
 require(sum(r['keysym']=='Home' for r in audit)==1,'one Home')
 require(read('primary/host/exit.json')['code']==0 and all(r['returncode'] is not None for r in read('primary/cleanup.json')),'terminal cleanup')
 result=read('native/result.json');require(result['status']=='PASS','native checks')
 for suite in result['suites']:
  require(suite['returncode']==0,'native suite exit')
  for log in suite['logs'].values():require(hashlib.sha256(files['native/'+log['file']]).hexdigest()==log['sha256'],'native log hash')
 print(json.dumps({'status':'PASS','members':len(files),'calls':7,'completed_input_programs':3,'refused_programs':1,'partial_input_repairs':1,'scope':'retained functional evidence; not pixels, readiness guarantee, latency or token costs'}))
if __name__=='__main__':main()
