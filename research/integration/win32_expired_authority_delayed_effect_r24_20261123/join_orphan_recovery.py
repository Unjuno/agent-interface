from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
PACKET=Path(__file__).resolve().parent; RAW=PACKET/'raw'; OUT=RAW/'orphan-recovery-join-r05'
if OUT.exists(): raise SystemExit('join output exists; refusing overwrite')
OUT.mkdir()
sys.path.insert(0,str(ROOT/'research/integration/standard_mcp_task_ledger_57_v1'))
from orphan_recovery_effect_handoff_v1 import adapt_orphan_recovery_effect

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x): p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8')
measured=read(RAW/'offline-reconstruction-r04/measured-run.json')
score=read(PACKET/'raw/recorder/effect-score-r24-offline.json')
raw=read(RAW/'interface_results-047e67d737ef4b889413a560669cf219.json')
action_public=json.loads(raw['result']['content'][0]['text'])
recovery=read(RAW/'orphan-recovery-api-attempt.json')
custody=recovery['custody_record']
recovery_raw=read(RAW/'recovery-mcp'/recovery['initial_recovery_receipt']['call_id']/'report.json')
joined=adapt_orphan_recovery_effect(measured=measured,action_public=action_public,recovery_envelope=recovery,recovery_raw_report=recovery_raw,effect_receipt=score,custody_record=custody)
write(OUT/'joined-effect-recovery.json',joined)
print(json.dumps({'source_action_status':joined['source_action']['status'],'recovery_status':joined['recovery_attempt']['status'],'factual_task_success':joined['effect']['factual_task_success'],'effect_timing':joined['effect']['effect_timing'],'eligible_task_success':joined['effect']['eligible_task_success'],'release_confirmed':joined['source_action']['release_confirmed'],'recovery_release_confirmed':joined['recovery_attempt']['release_confirmed']},indent=2))
