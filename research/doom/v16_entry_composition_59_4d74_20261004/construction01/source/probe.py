import sys,json,hashlib
from pathlib import Path
for d in ['doom','live_control','real_apps_v1','observation_tiles','observation_gating']:sys.path.insert(0,'/source/research/'+d)
import map01_overlap_controller_v39 as c
import session_map01_v16 as s
rows={name:{'path':m.__file__,'sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()} for name,m in list(sys.modules.items()) if getattr(m,'__file__',None) and str(m.__file__).startswith('/source/')}
result={'status':'PASS_IMPORT_ONLY','modules':rows,'controller_session_source':'session_map01_v12.py','game_instantiations':0,'provider_calls':0,'input_calls':0}
Path('/out/RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps({'status':result['status'],'loaded_source_modules':len(rows)}))
