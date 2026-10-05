"""One-shot real child-process test of exact V39 selection -> V15 stdin adapter."""
import ast, hashlib, json, os, queue, subprocess, sys, threading, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FREEZE=json.loads((ROOT/'FREEZE.json').read_text(encoding='utf-8'))
for rel,expected in FREEZE['files'].items():
    actual=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    if actual!=expected: raise SystemExit(f'freeze mismatch {rel}: {actual} != {expected}')

def selected_command(case, runtime):
    source=(ROOT/case/'research'/'doom'/'map01_overlap_controller_v39.py').read_bytes()
    tree=ast.parse(source)
    node=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='session_command')
    module=ast.Module(body=[node],type_ignores=[])
    ns={'sys':sys,'HERE':ROOT/case/'research'/'doom'}
    exec(compile(module,'frozen-v39-session-command','exec'),ns)
    args=type('Args',(),{'seed':990605,'load_fixture_manifest':ROOT/'fixture.json','measurement_session':True})()
    return ns['session_command'](args,runtime)

def run_arm(label):
    case=ROOT/label; runtime=ROOT/'results'/label/'scorer'; runtime.parent.mkdir(parents=True,exist_ok=False)
    selected=selected_command(label,runtime)
    if Path(selected[1]).name!='session_map01_v15.py': raise SystemExit(f'{label}: V15 not selected: {selected}')
    actual=[sys.executable,str(ROOT/'bootstrap.py'),selected[1],*selected[2:]]
    proc=subprocess.Popen(actual,cwd=case/'research'/'doom',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    lines=[]; notices=queue.Queue()
    def capture():
        for line in proc.stdout:
            lines.append(line.rstrip('\r\n')); notices.put(line)
        notices.put(None)
    reader=threading.Thread(target=capture,daemon=True); reader.start()
    try:
        ready=notices.get(timeout=5)
        if ready is None: raise RuntimeError(f'{label}: child exited before ready')
        ready_obj=json.loads(ready)
        if ready_obj.get('event')!='ready': raise RuntimeError(f'{label}: unexpected first child row {ready_obj}')
        time.sleep(.100)
        sent=False
        if proc.poll() is None:
            try:
                proc.stdin.write('{"op":"finish"}\n'); proc.stdin.flush(); sent=True
            except (BrokenPipeError,OSError): sent=False
        if proc.poll() is None: proc.stdin.close()
        try: code=proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate(); code=proc.wait(timeout=2)
            raise RuntimeError(f'{label}: child exceeded five-second bound')
        reader.join(timeout=2)
        if reader.is_alive(): raise RuntimeError(f'{label}: stdout reader did not stop')
        stderr=proc.stderr.read()
        (runtime.parent/'child-stdout.jsonl').write_text('\n'.join(lines)+('\n' if lines else ''),encoding='utf-8')
        (runtime.parent/'child-stderr.txt').write_text(stderr,encoding='utf-8')
    except BaseException:
        if proc.poll() is None: proc.terminate(); proc.wait(timeout=2)
        raise
    events=[json.loads(line) for line in lines]
    commands=[row for row in events if row.get('event')=='command']
    scheduler=None
    summary=runtime/'scorer-summary.json'
    if summary.exists(): scheduler=json.loads(summary.read_text(encoding='utf-8')).get('scheduler')
    return {'arm':label,'selected_command':selected,'bootstrap_command':actual,'pid':proc.pid,'exit_code':code,
      'ready_event':ready_obj,'stdout_lines':lines,'stderr':stderr,'sent_delayed_command':sent,
      'command_events':commands,'scheduler':scheduler}

results=[]
for label in ('baseline','candidate'):
    results.append(run_arm(label))
base,cand=results
if base['exit_code']==0 or 'WinError 10093' not in base['stderr'] or base['command_events']:
    raise SystemExit('baseline did not reproduce expected Windows pipe readiness failure')
if cand['exit_code']!=0 or not cand['sent_delayed_command'] or len(cand['command_events'])!=1:
    raise SystemExit('candidate child did not complete exactly one delayed command')
row=cand['command_events'][0]
if row['parsed_command']!={'op':'finish'} or json.loads(row['line'])!={'op':'finish'} or row['command_thread_id']!=row['polling_owner_thread_id']:
    raise SystemExit('candidate command identity or owner-thread mismatch')
if not row['sample_thread_ids'] or set(row['sample_thread_ids'])!={row['command_thread_id']}:
    raise SystemExit('candidate scorer sampling left the session owner thread')
if row['periodic_samples']<2 or not cand['scheduler'] or cand['scheduler'].get('samples',0)<2:
    raise SystemExit('candidate did not produce multiple periodic samples before command')
result={'schema':'v39-v15-real-child-pipe-construction-result-v1','main_sha':FREEZE['main_sha'],'candidate_sha':FREEZE['candidate_sha'],'python':sys.version,'platform':sys.platform,'arms':results,'decision':'PASS_V39_SELECTION_V15_CHILD_PIPE_SCOPED'}
(ROOT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('PASS_V39_SELECTION_V15_CHILD_PIPE_SCOPED')
for arm in results:
    print(f"{arm['arm']}: exit={arm['exit_code']} selected={Path(arm['selected_command'][1]).name} sent={arm['sent_delayed_command']} commands={len(arm['command_events'])} periodic_samples={arm['scheduler'].get('samples') if arm['scheduler'] else 'n/a'}")
