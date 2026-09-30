import copy,hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
repo=root.parents[2];sys.path.insert(0,str(repo))
manifest=json.loads((root/'manifest.json').read_text())
def require(ok,message):
 if not ok:raise ValueError(message)
for name,digest in manifest['files'].items():
 require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'file hash: '+name)
require(hashlib.sha256((repo/'runtime/core_v1/sequence.py').read_bytes()).hexdigest()==manifest['sequence_sha256'],'expansion source changed; use pinned source for this evidence')
a={};exec(compile((root/'candidate.py').read_bytes(),'archived_source_projection','exec'),a)
b={};exec(compile((root/'paced_candidate.py').read_bytes(),'paced_candidate','exec'),b)
size=lambda v:len(b['encode'](v))
old=json.loads((root/'result.json').read_text())
new=json.loads((root/'paced-result.json').read_text())
checked=0
for row in new['rows']:
 i=row['attempt']
 reply=json.loads((root/('reply-'+str(i)+'.json')).read_text())
 view=json.loads(next(c['text'] for c in reply['result']['content'] if c['type']=='text'))
 original=copy.deepcopy(view)
 projected=b['paced_projection'](view,a['brief_public_report'])
 require(view==original,'input mutated')
 require(size(view)==row['full_bytes'] and size(projected)==row['candidate_bytes'],'byte counts')
 require(projected==json.loads((root/('paced-projection-'+str(i)+'.json')).read_text()),'saved projection')
 require(size(a['brief_public_report'](view))==next(r['candidate_bytes'] for r in old['rows'] if r['attempt']==i),'old candidate recount')
 for key in ('outcome_summary','image_reference','session'):
  require(projected[key]==view[key],'changed '+key)
 for mutation in ('execution_failed','release_failed','wait_failed','wait_missing','wait_extra_field','wait_wrong_index','wait_negative_duration','mapping_missing','completed_missing','image_missing'):
  v=copy.deepcopy(view);raw=v['receipt']['source']['raw_report'];ex=raw['result']['execution']
  if mutation=='execution_failed':raw['result']['status']='execution_failed'
  elif mutation=='release_failed':ex['releases'][0]['verified']=False
  elif mutation=='wait_failed':ex['waits'][0]['completed']=False
  elif mutation=='wait_missing':ex['waits'].pop()
  elif mutation=='wait_extra_field':ex['waits'][0]['new_condition']='preserve'
  elif mutation=='wait_wrong_index':ex['waits'][0]['operation_index']=0
  elif mutation=='wait_negative_duration':ex['waits'][0]['ended_ns']=0
  elif mutation=='mapping_missing':raw['compilation']['operation_sources'].pop()
  elif mutation=='completed_missing':ex['completed_ops'].pop()
  elif mutation=='image_missing':v['image_status']='missing'
  require(b['paced_projection'](v,a['brief_public_report'])==v,'changed abnormal evidence: '+mutation)
  checked+=1
print(json.dumps({'status':'PASS','replies':len(new['rows']),'full_fallback_controls':checked,'scope':'offline byte/projection checks; no transport/model performance claim'}))
