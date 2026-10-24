from __future__ import annotations
import datetime as dt, hashlib, importlib.util, json, platform, subprocess, sys
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
C=json.loads((P/'conditions.json').read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
out={'schema':'win32-r43-preflight-v1','attempt_id':C['attempt_id'],'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'conditions_sha256':sha(P/'conditions.json'),'native_input_sent':False,'checks':{}}
try:
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    tracked=subprocess.run(['git','status','--porcelain=v1','--untracked-files=no'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    out.update(source_commit=head,tracked_status=tracked,python=sys.version,platform=platform.platform(),host=platform.node())
    out['checks']['native_windows']=sys.platform=='win32'
    out['checks']['source_commit_matches']=head==C['source_commit']
    out['checks']['tracked_tree_clean']=not tracked
    actual={name:sha(P/name) for name in C['frozen_files']}
    out['frozen_files']=actual; out['checks']['frozen_packet_hashes_match']=actual==C['frozen_files']
    runtime={name:sha(ROOT/name) for name in C['runtime_source_sha256']}
    out['runtime_source_sha256']=runtime; out['checks']['runtime_source_hashes_match']=runtime==C['runtime_source_sha256']
    pred={name:sha(ROOT/item['path']) for name,item in C['predecessor_hashes'].items()}
    out['predecessor_hashes']=pred; out['checks']['predecessors_match']=pred=={name:item['sha256'] for name,item in C['predecessor_hashes'].items()}
    absent=['run','task_raw.json','audit_r43.json','phases.json','PRERUN_CUSTODY.json','SHA256SUMS']
    out['existing_outputs']=[name for name in absent if (P/name).exists()]
    out['checks']['all_attempt_outputs_absent']=not out['existing_outputs']
    marker=P/'run'/'phase2_task'/'phase2-foreground.json'
    out['checks']['foreground_marker_absent']=not marker.exists()
    out['checks']['mcp_sdk_available']=importlib.util.find_spec('mcp') is not None
    out['checks']['attempt_id_matches_schema']=C['schema']=='win32-supervised-task-oracle-r43-v1' and C['attempt_id'].startswith('win32-supervised-task-oracle-20261024-r43-')
    out['status']='PASS' if all(out['checks'].values()) else 'FAIL_OR_UNKNOWN'
except BaseException as e:
    out['status']='FAIL_OR_UNKNOWN'; out['error']={'type':type(e).__name__,'detail':str(e)}
(P/'preflight.json').write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'checks':out['checks'],'native_input_sent':False},sort_keys=True))
raise SystemExit(0 if out['status']=='PASS' else 1)
