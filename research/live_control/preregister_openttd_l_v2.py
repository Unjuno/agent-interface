"""Freeze the corrected OpenTTD L-objective negative and fixed-Astra episodes."""
import hashlib,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/'results/timing-envelope-openttd-l-02'
SOURCES=['preregister_openttd_l_v2.py','openttd_negative_finish_l_v2.py','openttd_finish_outcome_v1.py','timing_envelope_openttd_l_driver_v2.py','timing_envelope_openttd_l_supervisor_v2.py','timing_envelope_v1.py','timing_envelope_v2.py','openttd_proposal_schema_v5.py','model_pair_runner_v2.py','pointer_socket_entry_v8.py','session_v22.py','openttd_contact_sheet_v1.py']
TASK_SOURCES=['openttd_task/interactive_l_v1.py','openttd_task/guarded_l_score_v1.py','openttd_task/observer_l_v1/common.nut','openttd_task/observer_l_v1/main.nut','openttd_task/observer_l_v1/info.nut','openttd_task/results/l-geometry-01/manifest.json','openttd_task/results/l-geometry-01/audit.json','openttd_task/results/l-geometry-01/baseline.sav']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
ROOT.mkdir(parents=True,exist_ok=False)
plan={'study':'timing-envelope-openttd-l-02','status':'PREREGISTERED_BEFORE_EXECUTION','execution_order':['negative-control','fixed-astra'],
      'task_allocation':{'seed':991003,'save_sha256':'c91ea76b4dc8c280f98de2e3a4c9b34d6033c833a34fc401bd0c076a15b4bc5b','target_tiles':[977,978,979,1043,1107],'forbidden_tiles':[1041,1042,1105,1106],
                         'objective':'five-tile L, ordered A-to-B horizontal then B-to-C vertical, two straight drags expected but not prescribed','toolbar':'closed','max_model_turns':12,'evaluator':'geometry-derived independent guarded_l_score_v1'},
      'negative_control':{'model_calls':0,'task_input_calls':0,'expected_engine_success':False,'expected_failure_mode':'visual_verify_false_positive'},
      'positive_path':{'model_route':'all turns gpt-6-astra medium','hard_success_gate':'model verify plus independent evaluator success'},
      'primary_measurements':['hard task success','initial observation to semantic completion','wrapper-observed model wait','proposal publication to first useful feedback','model calls and reported token usage','durable calls, exact frames and contact sheets'],
      'failure_policy':'retain the first bounded, stopped or typed independent failure and do not retry',
      'version_reason':'new allocation after v1 harness failure; corrected driver removes caller id and restores final observation plus duration-derived timeout',
      'interpretation_limit':'one new objective-structure episode; no general route, latency distribution, human comparison or speedup claim',
      'sources':{**{n:digest(HERE/n) for n in SOURCES},**{n:digest(HERE.parent/n) for n in TASK_SOURCES}}}
path=ROOT/'preregistration.json';temporary=path.with_suffix('.json.tmp');temporary.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path);print(path)

