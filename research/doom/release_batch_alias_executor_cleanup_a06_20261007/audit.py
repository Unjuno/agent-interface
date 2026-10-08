#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--raw',required=True); p.add_argument('--freeze',required=True); a=p.parse_args()
f=json.loads(Path(a.freeze).read_text(encoding='utf-8'))
rawp=Path(a.raw); raw=json.loads(rawp.read_text(encoding='utf-8'))
checks={}
c=raw.get('case',{})
checks['schema']=raw.get('schema')=='v39-v15-v13-alias-cleanup-a06-raw-v1'
checks['alias_precondition']=c.get('resolved_alias_keycodes')=={'a':38,'A':38}
checks['executor_terminal_failed']=c.get('executor_terminal',{}).get('status')=='failed'
checks['owner_cleanup_verified']=c.get('executor_terminal',{}).get('release',{}).get('verified') is True
checks['fake_server_neutral']=c.get('server_keycodes_down_after_executor_cleanup')==[]
checks['owner_close_ok']=c.get('owner_close_error') is None
checks['no_live_claims']=raw.get('claims')=={'real_x11':False,'gui':False,'doom':False,'model':False,'physical_keyboard':False,'application_effect':False}
result={'schema':'a06-audit-v1','outcome':'PASS_METHOD_SCOPED' if all(checks.values()) else 'FAIL','checks':checks,'raw_sha256':hashlib.sha256(rawp.read_bytes()).hexdigest()}
Path(f['audit_path']).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,sort_keys=True))
