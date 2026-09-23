import json,hashlib,time,tempfile,shutil,statistics
from pathlib import Path
from agent_review import review_native
source=Path('results-local/native-main-use-01/run').resolve()
out=Path('results-local/native-review-profile-01')
linux=Path(tempfile.mkdtemp(prefix='agent-interface-review-',dir='/tmp'))
report=json.loads((source/'reply-2.json').read_bytes())
image=Path(report['observation']['native']['artifact']['path']);relative=image.relative_to(source)
(linux/relative).parent.mkdir(parents=True)
shutil.copyfile(source/'reply-2.json',linux/'reply-2.json');shutil.copyfile(image,linux/relative)
original_hash=hashlib.sha256((source/'reply-2.json').read_bytes()).hexdigest()
rows=[]
for i in range(8):
 for label,root in ([('windows_mount',source),('linux_tmp',linux)] if i%2==0 else [('linux_tmp',linux),('windows_mount',source)]):
  t=time.perf_counter_ns()
  result=review_native(root/'reply-2.json',root,compact=True,recorded_run_directory=str(source))
  elapsed=(time.perf_counter_ns()-t)/1e6
  assert result['image_status']=='image'
  assert result['receipt']['source']['sha256']==original_hash
  assert result['image_reference']['sha256']==report['observation']['native']['artifact']['sha256']
  rows.append({'round':i,'location':label,'review_ms':elapsed})
assert hashlib.sha256((source/'reply-2.json').read_bytes()).hexdigest()==original_hash
record={'source_sha256':original_hash,'image_sha256':report['observation']['native']['artifact']['sha256'],'linux_copy':str(linux),'rows':rows,'medians_ms':{key:statistics.median(r['review_ms'] for r in rows if r['location']==key) for key in ['windows_mount','linux_tmp']},'scope':'alternating historical reads with explicit archive mapping at both locations; current machine and path lengths differ; no model or live-action latency claim'}
(out/'filesystem-comparison.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
