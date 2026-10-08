"""Read-only retained evidence validation, no dispatch or extraction."""
import base64,hashlib,io,json,tarfile,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
def require(value,message):
 if not value:raise ValueError(message)
def main():
 manifest=json.loads((ROOT/'manifest.json').read_text())
 with tarfile.open(ROOT/'raw.tar.gz') as tar:
  files={m.name:tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
 require(set(files)==set(manifest),'member set')
 for name,data in files.items():
  require(len(data)==manifest[name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[name]['sha256'],name)
 def read(name):return json.loads(files[name])
 def view(prefix,i):
  reply=read(f'{prefix}/host/reply-{i}.json')
  require(reply['status']=='returned','transport returned')
  return json.loads(next(c['text'] for c in reply['result']['content'] if c['type']=='text'))
 for prefix,tools,reviewed in [('calc',['observe','dispatch','dispatch','review_target','dispatch','inspect_target','close'],[1,2,3,4,5,6]),('child-target',['observe','dispatch','dispatch','dispatch','close'],[1,2,4]),('managed-target',['observe','dispatch','dispatch','close'],[1,2,3])]:
  require([read(f'{prefix}/host/request-{i}.json')['tool'] for i in range(1,len(tools)+1)]==['interface_'+t for t in tools],'call order')
  require(read(prefix+'/host/exit.json')['code']==0,'transport closed')
  require(all(x['returncode'] is not None for x in read(prefix+'/cleanup.json')),'processes terminal')
  require(read(prefix+'/evaluation.json')['success'] is True,'saved effect evaluation')
  for i in reviewed:
   b=files[f'{prefix}/host/reply-{i}.json'];reply=json.loads(b);review=read(f'{prefix}/host/review-{i}.json')
   require(review['reply_sha256']==hashlib.sha256(b).hexdigest(),'review reply binding')
   images=[hashlib.sha256(base64.b64decode(c['data'],validate=True)).hexdigest() for c in reply['result']['content'] if c['type']=='image']
   require(images==[x['sha256'] for x in review['images']] and len(images)==1,'review image binding')
 for prefix in ['child-target','managed-target']:
  require(read(prefix+'/left-effect.json')=={'saved':True,'text':'http://p_q'},'left effect')
  require(prefix+'/right-effect.json' not in files and prefix+'/right-events.jsonl' not in files,'right untouched')
  rows=[json.loads(x) for x in files[prefix+'/left-events.jsonl'].decode().splitlines()]
  text=''.join(x['char'] for x in rows if x.get('bindtag')=='AgentInterfacePassiveAudit' and x.get('char') and x['char'].isprintable())
  require(text=='http://p_q','one text input in passive audit')
  failure=view(prefix,2)
  require(failure['outcome_summary']['execution_status']=='completed' and failure['outcome_summary']['input_release_verified'] is True,'completed input retained')
  require('outside configured transient family' in failure['post_dispatch_inspection']['error'],'foreign family error')
  require(failure['receipt']['schema']=='agent-interface/receipt-view-v3-report-ref','error full fallback')
 refused=view('child-target',3)
 require(refused['outcome_summary']['execution_status']=='refused' and refused['post_dispatch_inspection']['status']=='skipped','bad schema skipped inspection')
 require('error' in view('child-target',4)['post_dispatch_inspection'],'child target limitation retained')
 success=view('managed-target',3);context=success['post_dispatch_inspection']
 require(success['receipt']['schema']=='agent-interface/receipt-view-dispatch-summary-v1','successful summary')
 require('error' not in context and context['review_request']['tool']=='interface_review_target','review candidate')
 require(context['input_dispatched'] is False and context['authority_granted'] is False,'metadata only')
 require(success['session']['binding_revision']==1,'no automatic rebind')
 report=read('managed-target/mcp/'+success['call_id']+'/report.json')
 require(report['post_dispatch_inspection']==context,'complete context preserved')
 require(context['started_ns']>=report['result']['execution']['ended_ns'] and context['ended_ns']>=context['started_ns'],'post-dispatch order')
 calc=view('calc',3)['post_dispatch_inspection'];review_request=read('calc/host/request-4.json')
 require(all(review_request['arguments'][k]==v for k,v in calc['review_request']['arguments'].items()),'explicit modal review uses bundled candidate')
 with zipfile.ZipFile(io.BytesIO(files['calc/saved.xlsx'])) as z:sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
 ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 cells={c.attrib['r']:c.find('s:v',ns).text for c in sheet.findall('.//s:c',ns) if c.find('s:v',ns) is not None}
 require(cells.get('A1')=='862' and cells.get('A2')=='506','Calc saved values')
 require(read('interrupted/restart-interruption.json')['status']=='interrupted_before_primary_control','interruption retained')
 require(not any(n.startswith('interrupted/host/') for n in files),'no primary requests before interruption')
 for prefix in ['native-01','native-02']:
  result=read(prefix+'/result.json');require(result['status']=='PASS','native result')
  for suite in result['suites']:
   require(suite['returncode']==0,'suite exit')
   for log in suite['logs'].values():require(hashlib.sha256(files[prefix+'/'+log['file']]).hexdigest()==log['sha256'],'suite log hash')
 print(json.dumps({'status':'PASS','members':len(files),'scope':'retained call/effect/inspection/image identity; not pixel understanding, performance or model costs'}))
if __name__=='__main__':main()
