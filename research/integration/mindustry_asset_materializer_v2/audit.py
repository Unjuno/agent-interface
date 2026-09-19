#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
f=json.loads((R/'fixture.json').read_text()); r=json.loads((R/'RESULT.json').read_text()); ids=f['test']
controls=r['controls']; good=r['good']
expected_manifest={'schema':'mindustry_asset_materialized_v1','status':'ASSETS_READY','files':{
 'jar':{'name':ids['jar']['name'],'bytes':ids['jar']['bytes'],'sha256':ids['jar']['sha256']},
 'save':{'name':ids['save']['name'],'bytes':ids['save']['bytes'],'sha256':ids['save']['sha256']}}}
recomputed={
 'formal':r['formal_invocation']==1 and r['formal_reruns']==0,
 'decision':r['decision']=='PASS_MINDUSTRY_ASSET_MATERIALIZER_MECHANICS_SCOPED',
 'manifest':good['manifest']==good['manifest_file']==expected_manifest,
 'jar':good['jar']=={'bytes':ids['jar']['bytes'],'sha256':ids['jar']['sha256']},
 'save':good['save']=={'bytes':ids['save']['bytes'],'sha256':ids['save']['sha256']},
 'files':good['published_files']==['MANIFEST.json',ids['jar']['name'],ids['save']['name']],
 'controls':all(controls[k]['error'] is not None and controls[k]['cleanup']['clean'] for k in ('wrong_jar','wrong_save','symlink_jar','preexisting_output')),
 'production_metadata':r['production_identities']==f['production'],
 'gates_all':all(r['gates'].values()),
}
out={'schema':'mindustry_asset_materializer_audit_v2','passed':all(recomputed.values()),'checks':recomputed,'decision':r['decision']}
(R/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['passed'] else 1)
