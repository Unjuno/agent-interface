import argparse,hashlib,json,os,platform,shutil,subprocess,sys
from pathlib import Path
from harness import prompt,prompt_diff,parse_answer,extract_jsonl
TASK='MODEL-BRANCH-K1K2-HARNESS-READINESS-20260918-001'
RUNNER_BLOBS={'model_text_runner_v1.py':'5a751ec3e7a6f8f67759f09bfebe2433509eabe9','model_pair_runner_v2.py':'31a9911b9bf21418143fd32f1d821a40ca2f2af8'}

def first_existing(paths):
    for p in paths:
        if p and Path(p).is_file(): return str(Path(p).resolve())
    return None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=Path(a.out)
    if out.exists(): raise SystemExit('result exists')
    d=prompt_diff()
    prompts={str(k):{'bytes':len(prompt(k).encode()),'sha256':hashlib.sha256(prompt(k).encode()).hexdigest()} for k in (1,2)}
    node=shutil.which('node')
    codex_cmd=shutil.which('codex')
    cli=first_existing([
        os.environ.get('CODEX_CLI_JS'),
        '/mnt/c/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js',
        '/opt/nvm/versions/node/v22.16.0/lib/node_modules/@openai/codex/bin/codex.js'])
    node_version=None
    if node:
        q=subprocess.run([node,'--version'],capture_output=True,text=True,timeout=5);node_version=q.stdout.strip() if q.returncode==0 else None
    # Parser/extractor controls are re-exercised inside formal without any provider call.
    sample1='{"branches":[{"branch_id":"b1","predicate":"LEFT","semantic_action":"CONTINUE_LEFT","no_authority":true}]}'
    sample2='{"branches":[{"branch_id":"b1","predicate":"LEFT","semantic_action":"CONTINUE_LEFT","no_authority":true},{"branch_id":"b2","predicate":"RIGHT","semantic_action":"CONTINUE_RIGHT","no_authority":true}]}'
    parser_ok=(len(parse_answer(sample1,1)['branches'])==1 and len(parse_answer(sample2,2)['branches'])==2)
    lines=[json.dumps({'type':'thread.started'}),json.dumps({'type':'item.completed','item':{'type':'agent_message','text':sample1}}),json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':20,'output_tokens':10,'reasoning_output_tokens':0}})]
    usage_ok=extract_jsonl(lines,1000,[1100,1200,1300])['wall_to_message_ns']==200
    static_ok=(d['same_length'] and d['diff_count']==1 and d['bytes']==[(49,50)] and parser_ok and usage_ok)
    runtime_ready=bool(node and (codex_cmd or cli))
    result={
      'task':TASK,'formal_invocations':1,'reruns':0,'python':platform.python_version(),'node_path':node,'node_version':node_version,
      'codex_command':codex_cmd,'codex_cli_js':cli,'runner_blobs':RUNNER_BLOBS,
      'prompt_diff':d,'prompts':prompts,'generations_per_arm':{'K1':1,'K2':1},'k2_second_branch_via_extra_generation':False,
      'parser_no_authority_ok':parser_ok,'usage_arrival_extractor_ok':usage_ok,'static_harness_ok':static_ok,'runtime_ready':runtime_ready,
      'model_calls':0,'provider_actions':0,'network_actions':0,'gui_actions':0,'task_input_actions':0}
    if not static_ok: result['decision']='FAIL_HARNESS_ISOLATION'
    elif not runtime_ready: result['decision']='HOLD_MODEL_RUNTIME_UNAVAILABLE'
    else: result['decision']='PASS_MODEL_BRANCH_MATCHED_HARNESS_READY_SCOPED'
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
