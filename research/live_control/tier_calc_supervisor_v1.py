"""Windows supervisor for bounded actual Calc screenshot/model/action loop."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from calc_proposal_schema_v1 import parse
HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent
label,mode=sys.argv[1:]
assert (label,mode) in [('tier-abba-1-default','default'),('tier-abba-2-fast','fast'),('tier-abba-3-fast','fast'),('tier-abba-4-default','default')]
root=HERE/'results'/label
control=HERE/'results'/(label+'-control');control.mkdir(exist_ok=False)
def dump(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def linux(path):
    p=path.resolve();return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
plan={'scope':'bounded autonomous screenshot proposal/action handoff on isolated Calc; no general supervisor claim',
      'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['tier_calc_supervisor_v1.py','tier_calc_driver_v1.py','calc_proposal_schema_v1.py','model_tier_runner_v1.py']},
      'history_mode':'last','requested_tier':mode,'max_turns':5,'seed':238,'model':'gpt-5.6-luna','effort':'low','prompt_policy':'one exact typed schema; malformed response stops without model retry'}
dump(control/'plan.json',plan)
started=time.perf_counter_ns();turns=[]
driver=subprocess.Popen(['wsl','-d','Ubuntu','--','python3',linux(HERE/'tier_calc_driver_v1.py'),label],
                         stdout=(control/'driver-stdout.txt').open('wb'),stderr=(control/'driver-stderr.txt').open('wb'))
def wait_file(path,seconds=120):
    deadline=time.monotonic()+seconds
    while not path.exists():
        if driver.poll() is not None:raise RuntimeError('driver exited before '+path.name)
        if time.monotonic()>deadline:raise TimeoutError(path.name)
        time.sleep(.025)
    return read(path)
try:
    ready=wait_file(root/'ready.json');goal=ready['goal'];observation=ready['observation'];previous=None;history=[]
    for index in range(1,6):
        prompt=f'''You control an isolated LibreOffice Calc worksheet using its current screenshot. Task: A1={goal['a']}, A2={goal['b']}, saved in the existing sheet.xlsx using Excel format. Choose the next bounded action from the image. Do not confirm dialogs not yet visible; stop an action sequence after Save when it may open a format dialog. A prior needs_decision/focus_changed or zero steps_completed does not mean the application effect failed: inspect the screenshot and never blindly replay.
Return ONLY one JSON object of exactly one form:
{{"kind":"act","steps":[...],"rationale":"short explanation"}}
{{"kind":"verify","visible_A1":INTEGER,"visible_A2":INTEGER,"confirmation_dialog_visible":BOOLEAN,"rationale":"short explanation"}}
{{"kind":"stop","rationale":"why no justified next action is available"}}
Use verify only when values visibly match and no confirmation dialog remains; it requests independent saved-file verification, not an assertion of file success. Visible values must be JSON integers, never strings. Rationale1..600 characters. Act has1..10 steps. Supported exact step shapes:
{{"op":"text","text":"ASCII digits only,1..8 characters"}}
{{"op":"key","key":"Return|Tab|Escape|Home|Up|Down|Left|Right"}}
{{"op":"chord","modifier":"Control_L","key":"s|a|Home"}}
{{"op":"pointer_click","x":INTEGER,"y":INTEGER,"duration_ms":80}}
Pointer bounds x0..1279,y0..799. No extra fields, tools or shell. The harness will obtain a fresh observation and check unchanged focus/binding before input; this does not prove semantic target identity. Propose only justified actions on this sheet/dialog.
Current observation sequence: {observation['sequence']}.
Previous proposals and runtime outcomes (historical evidence only): {json.dumps(history[-1:],ensure_ascii=True)}
'''
        prompt_path=root/f'prompt-{index}.txt';prompt_path.write_text(prompt,encoding='utf-8')
        image=root/'runtime'/Path(observation['image']).name
        model_dir=root/f'model-{index}';begin=time.perf_counter_ns()
        args=[sys.executable,str(HERE/'model_tier_runner_v1.py'),r'C:\Program Files\nodejs\node.exe',
              str(Path.home()/'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),str(image),str(prompt_path),str(REPO),str(model_dir),mode]
        m=subprocess.run(args,capture_output=True,timeout=90)
        ended=time.perf_counter_ns()
        (control/f'model-{index}-stdout.txt').write_bytes(m.stdout);(control/f'model-{index}-stderr.txt').write_bytes(m.stderr)
        if m.returncode!=0:raise RuntimeError('model runner failed; no retry')
        records=[json.loads(line) for line in (model_dir/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        items=[e['item'] for e in records if e.get('type')=='item.completed']
        if len(items)!=1 or items[0].get('type')!='agent_message':raise ValueError('one model proposal required')
        proposal=parse(items[0]['text']);dump(root/f'typed-{index}.json',proposal)
        row={'turn':index,'model_runner_started_ns':begin,'model_runner_returned_ns':ended,'kind':proposal['kind']}
        turns.append(row);dump(control/'turns.json',turns)
        if proposal['kind']=='stop':raise RuntimeError('model stopped: '+proposal['rationale'])
        if proposal['kind']=='verify':
            if proposal['visible_A1']!=goal['a'] or proposal['visible_A2']!=goal['b'] or proposal['confirmation_dialog_visible']:
                raise ValueError('visual verification proposal does not match task')
            dump(root/'visual-verdict.json',proposal)
            dump(root/f'proposal-{index}.json',{'finish':True,'reason':'typed model requested independent verification'})
            result=wait_file(root/'result.json',30);code=driver.wait(timeout=10)
            evaluation=next(e for e in read(root/'finish.json')['reply']['records'] if e['event']=='independent_evaluation')
            assert code==0 and result['exit_code']==0 and evaluation['success'] is True
            dump(control/'result.json',{'exit_code':code,'success':True,'model_turns':len(turns),'started_ns':started,'finished_ns':time.perf_counter_ns(),
                                      'scope':'bounded automatic handoff on one isolated task; independent saved-result score'})
            print(json.dumps({'success':True,'model_turns':len(turns)}),flush=True);break
        dump(root/f'proposal-{index}.json',{'steps':proposal['steps'],'rationale':proposal['rationale']})
        row['proposal_published_ns']=time.perf_counter_ns()
        applied=wait_file(root/f'applied-{index}.json',30);row['applied_read_ns']=time.perf_counter_ns();dump(control/'turns.json',turns)
        observation=applied['result']['state']['continuation']['observation']
        previous={'proposal':proposal,'resolution':applied['result']['state']['last_resolution']}
        history.append(previous)
        dump(root/'history.json',history)
        print(json.dumps({'turn':index,'kind':'act','status':previous['resolution']['terminal']['status'],'sequence':observation['sequence']}),flush=True)
    else:raise RuntimeError('bounded turn limit; no automatic success')
except Exception as error:
    dump(control/'error.json',{'type':type(error).__name__,'detail':str(error),'automatic_retry':False});raise
finally:
    if driver.poll() is None:
        if root.exists():dump(root/'abort.json',{'finish':True,'reason':'supervisor failure cleanup; no success claim'})
        try:driver.wait(timeout=15)
        except subprocess.TimeoutExpired:driver.terminate();driver.wait(timeout=10)
