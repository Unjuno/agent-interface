import base64,hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def require(ok,label):
 if not ok:raise ValueError(label)
def main():
 manifest=json.loads((ROOT/'manifest.json').read_bytes())
 with tarfile.open(ROOT/'raw.tar.gz') as t:files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
 require(set(files)==set(manifest),'members')
 for name,data in files.items():require(len(data)==manifest[name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[name]['sha256'],name)
 def read(n):return json.loads(files[n])
 p='cli-summary-primary-01/'
 for i in [2,3,4]:
  view=read(p+f'stdout-{i}.json');raw=read(p+f'call-{i}/report.json');data=files[p+f'call-{i}/report.json'];source=view['receipt']['source'];ex=raw['result']['execution']
  require(view['receipt']['schema']=='agent-interface/receipt-view-dispatch-summary-v1','summary')
  require(view['outcome_summary']['execution_status']=='completed' and view['outcome_summary']['input_release_verified'] is True,'completed/released')
  require(source['sha256']==hashlib.sha256(data).hexdigest() and source['bytes']==len(data),'exact raw identity')
  require(view['retention']['report_persisted'] is True and view['retention']['replay_allowed'] is False,'retention')
  summary=view['receipt']['execution_summary']
  for key in ['observations','releases','activations','started_ns','ended_ns','program_emissions']:require(summary[key]==ex[key],'retained execution '+key)
  require(summary['completed_operation_count']==len(ex['completed_ops']),'completed count')
  require(summary['wait_summary']['requested_ms_total']==sum(w['requested_ms'] for w in ex['waits']),'wait total')
  require(view['presentation']['retrieve']['command']=='review' and view['presentation']['retrieve']['arguments']['report'].endswith(f'/call-{i}/report.json'),'CLI retrieval')
  require(read(p+f'host-{i}.json')['exit_code']==0,'CLI exit')
 for i in range(1,5):
  v=read(p+f'stdout-{i}.json');review=read(p+f'review-{i}.json');digest=hashlib.sha256(base64.b64decode(v['image']['data'],validate=True)).hexdigest()
  require(digest==v['image_reference']['sha256']==review['image_sha256'],'image/review identity')
  require(review['source_sha256']==v['receipt']['source']['sha256'],'review source')
 full=read(p+'retrieved-full.json');save=read(p+'stdout-4.json')
 require(full['image']==save['image'] and full['outcome_summary']==save['outcome_summary'],'full retrieval equality')
 require(all(read(p+'retrieval-check.json')[k] is True for k in ['report_unchanged','same_image','same_outcome','no_input']),'retrieval checks')
 require(read(p+'left-effect.json')=={'saved':True,'text':'http://e_f'} and read(p+'evaluation.json')['success'] is True,'saved effect')
 require(p+'right-events.jsonl' not in files and p+'right-effect.json' not in files,'right untouched')
 require(all(x['returncode'] is not None for x in read(p+'cleanup.json')),'fixture terminal')
 n='cli-summary-native-01/';native=read(n+'result.json');require(native['status']=='PASS','native status')
 for suite in native['suites']:
  require(suite['returncode']==0,'native exit')
  for log in suite['logs'].values():require(hashlib.sha256(files[n+log['file']]).hexdigest()==log['sha256'],'native log')
 print(json.dumps({'status':'PASS','files':len(files),'scope':'retained self-use evidence, not pixel interpretation or performance comparison'}))
if __name__=='__main__':main()
