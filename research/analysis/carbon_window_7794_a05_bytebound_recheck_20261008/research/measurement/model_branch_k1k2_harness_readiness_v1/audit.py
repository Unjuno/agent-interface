import argparse,hashlib,json
from pathlib import Path
EXPECTED={'model_text_runner_v1.py':'5a751ec3e7a6f8f67759f09bfebe2433509eabe9','model_pair_runner_v2.py':'31a9911b9bf21418143fd32f1d821a40ca2f2af8'}
def verify(r):
    e=[]
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0:e.append('invocation')
    d=r.get('prompt_diff',{})
    if not(d.get('same_length') and d.get('diff_count')==1 and d.get('bytes')==[[49,50]]):e.append('prompt_diff')
    if r.get('generations_per_arm')!={'K1':1,'K2':1} or r.get('k2_second_branch_via_extra_generation') is not False:e.append('generation_count')
    if r.get('parser_no_authority_ok') is not True:e.append('parser')
    if r.get('usage_arrival_extractor_ok') is not True:e.append('usage_extractor')
    if r.get('runner_blobs')!=EXPECTED:e.append('runner_source')
    if any(r.get(k)!=0 for k in ('model_calls','provider_actions','network_actions','gui_actions','task_input_actions')):e.append('forbidden_action')
    ready=bool(r.get('node_path') and (r.get('codex_command') or r.get('codex_cli_js')))
    expected='PASS_MODEL_BRANCH_MATCHED_HARNESS_READY_SCOPED' if ready and not e else ('HOLD_MODEL_RUNTIME_UNAVAILABLE' if not ready and not e else 'FAIL_HARNESS_ISOLATION')
    if r.get('runtime_ready')!=ready:e.append('runtime_flag')
    if r.get('decision')!=expected:e.append('decision')
    return {'audit_pass':not e,'errors':e,'expected_decision':expected}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');a=ap.parse_args();p=Path(a.result);r=json.loads(p.read_text());o=verify(r);o['result_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
