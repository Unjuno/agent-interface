#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
f=json.loads((R/'fixture.json').read_text()); r=json.loads((R/'RESULT.json').read_text())
prov=r['provenance']; expected_env=all(r['commands'].values()) and all(v['available'] for v in r['modules'].values()) and ('21.' in r['java'] or 'version "21' in r['java'])
jar_ready=any(x['identity_ok'] for x in r['jar_observations']); save_ready=any(x['identity_ok'] for x in r['save_observations'])
if not all(prov.values()): d='FAIL_PROVENANCE_MISMATCH'
elif not expected_env: d='HOLD_ENVIRONMENT_MISSING'
elif jar_ready and save_ready: d='PASS_ASSETS_READY'
else: d='HOLD_ASSETS_NOT_MATERIALIZED'
checks={'decision':d==r['decision'],'formal':r['formal_invocation']==1 and r['formal_reruns']==0,'env':expected_env==r['environment_ok'],'jar':jar_ready==r['jar_ready'],'save':save_ready==r['save_ready'],'provenance':f['jar']['repo_sha256']==f['jar']['official_sha256'] and f['jar']['repo_bytes']==f['jar']['official_bytes']}
out={'schema':'mindustry_live_smoke_asset_readiness_audit_v1','passed':all(checks.values()),'checks':checks,'decision':r['decision']}
(R/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['passed'] else 1)
