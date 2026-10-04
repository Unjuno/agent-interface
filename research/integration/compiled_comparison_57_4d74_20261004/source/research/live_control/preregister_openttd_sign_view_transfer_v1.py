"""Preregister a no-model OpenTTD sign-transparency view transform probe."""
import hashlib,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/'results/openttd-sign-view-transfer-01'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
SOURCES=['preregister_openttd_sign_view_transfer_v1.py','probe_openttd_sign_view_transfer_v1.py','audit_openttd_sign_view_transfer_v1.py','pointer_socket_entry_v9.py','durable_submit_v4.py','received_continuation_v1.py','received_exchange_v2.py','session_v22.py']
TASK=['openttd_task/interactive_v8.py','openttd_task/guarded_score_v2.py','openttd_task/results/geometry-01/baseline.sav']
ROOT.mkdir(parents=True,exist_ok=False)
plan={'study':'openttd-sign-view-transfer-01','status':'PREREGISTERED_BEFORE_EXECUTION','model_calls':0,'task':'load held-out seed-991002 straight-road geometry, make trees transparent, then apply Control_L+1 and compare the live view before/after before independently scoring','hypothesis':'the official station-sign transparency control also changes custom sign presentation on a second geometry without task mutation','expected':{'engine_success_remains_false':True,'all_target_and_forbidden_road_state_unchanged':True,'surrounding_road_owner_unchanged':True},'method_source':'OpenTTD official manual documents Ctrl+1 as station-sign transparency and lists Signs displayed as a separate display option','method_url':'https://wiki.openttd.org/en/Manual/Transparency%20options','classification':'held-out view-transform transfer only; no planner exposure','sources':{**{n:sha(HERE/n) for n in SOURCES},**{n:sha(HERE.parent/n) for n in TASK}},'scope':'second-geometry view-transform feasibility only; no model judgment, task success, latency or token claim'}
temporary=ROOT/'preregistration.json.tmp';temporary.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8');os.replace(temporary,ROOT/'preregistration.json');print(ROOT/'preregistration.json')
