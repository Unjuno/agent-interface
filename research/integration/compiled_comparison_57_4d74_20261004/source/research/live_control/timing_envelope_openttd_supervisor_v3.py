"""Windows supervisor for bounded actual OpenTTD screenshot/model/action loop."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from PIL import Image
from openttd_proposal_schema_v3 import parse
from timing_envelope_v1 import interval
from timing_envelope_v2 import Recorder
HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent
root=HERE/'results/timing-envelope-openttd-03'
control=HERE/'results/timing-envelope-openttd-control-03';control.mkdir(exist_ok=False)
def dump(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def linux(path):
    p=path.resolve();return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
plan={'scope':'fresh bounded OpenTTD loop with buffered process-scoped end-to-end timing envelope; no matched comparison yet',
      'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['timing_envelope_openttd_supervisor_v3.py','timing_envelope_openttd_driver_v3.py','timing_envelope_v1.py','timing_envelope_v2.py','openttd_proposal_schema_v3.py','model_pair_runner_v1.py','session_v10.py']},
      'max_turns':8,'seed_semantics':'canonical save; no RNG override','model':'gpt-5.6-luna','effort':'low','prompt_policy':'full-screen coordinate contract plus bounded delayed hover observation'}
dump(control/'plan.json',plan)
timing=Recorder(control/'timing-envelope.jsonl')
started=time.perf_counter_ns();timing.record('supervisor_started',timestamp_ns=started)
timing.record('runtime_receipt',state='NOT_RECORDED',cause='supervisor_started')
timing.record('os_injection',state='NOT_RECORDED',cause='runtime_receipt')
turns=[]
driver=subprocess.Popen(['wsl','-d','Ubuntu','--','python3',linux(HERE/'timing_envelope_openttd_driver_v3.py')],
                         stdout=(control/'driver-stdout.txt').open('wb'),stderr=(control/'driver-stderr.txt').open('wb'))
def wait_file(path,seconds=120):
    deadline=time.monotonic()+seconds
    while not path.exists():
        if driver.poll() is not None:raise RuntimeError('driver exited before '+path.name)
        if time.monotonic()>deadline:raise TimeoutError(path.name)
        time.sleep(.025)
    return read(path)
try:
    ready=wait_file(root/'ready.json');initial_detected=time.perf_counter_ns()
    initial_event=timing.record('initial_observation_detected',timestamp_ns=initial_detected,
                                uncertainty_ns=25_000_000,cause='supervisor_started',
                                details={'definition':'ready.json first detected by 25ms file poll'})
    task=ready['task'];observation=ready['observation'];previous=None
    for index in range(1,9):
        image=root/'runtime'/Path(observation['image']).name
        with Image.open(image) as opened:image_dimensions=[opened.width,opened.height]
        app_geometry=observation['pointer_binding']['geometry']
        prompt=f'''You control an isolated OpenTTD road fixture using its current screenshot. Task: {task} Choose the next bounded visual action. Use the road toolbar and straight-road tool when visible. If an icon's meaning is uncertain, use pointer_move followed by dwell_observe around 800ms so the delayed tooltip is captured before clicking; ordinary observe immediately after a move may be too early. A prior needs_decision/focus_changed or zero steps_completed does not mean the application effect failed: inspect the screenshot and never blindly replay.
Return ONLY one JSON object of exactly one form:
{{"kind":"act","steps":[...],"rationale":"short explanation"}}
{{"kind":"verify","road_visible":BOOLEAN,"rationale":"short explanation"}}
{{"kind":"stop","rationale":"why no justified next action is available"}}
Use verify only when the requested A-to-C road is visibly complete; it requests the independent engine guard score. Rationale1..600 characters. Act has1..6 steps. Supported exact step shapes:
{{"op":"pointer_move","x":INTEGER,"y":INTEGER}}
{{"op":"dwell_observe","delay_ms":100..2000}}
{{"op":"pointer_click","x":INTEGER,"y":INTEGER}}
{{"op":"pointer_drag","points":[{{"x":INTEGER,"y":INTEGER}},...],"duration_ms":80..1000}}
{{"op":"observe"}}
Coordinates are absolute in the full screenshot, not relative to the app. Full screenshot dimensions: {image_dimensions}. Active app geometry [left,top,width,height]: {app_geometry}. Valid pointer bounds are x0..{image_dimensions[0]-1},y0..{image_dimensions[1]-1}; remain inside the active app. No extra fields, keys, tools or shell. The harness obtains a fresh observation and checks unchanged focus/binding before input. Propose only actions justified by the current image.
Current observation sequence: {observation['sequence']}.
Previous proposal and runtime outcome: {json.dumps(previous,ensure_ascii=True)}
'''
        prompt_path=root/f'prompt-{index}.txt';prompt_path.write_text(prompt,encoding='utf-8')
        model_dir=root/f'model-{index}';begin=time.perf_counter_ns()
        timing.record('planner_request_started',timestamp_ns=begin,
                      cause='initial_observation_detected' if index==1 else 'first_useful_feedback_detected',
                      details={'turn':index,'image_sequence':observation['sequence']})
        timing.record('provider_request_received',state='NOT_RECORDED',
                      cause='planner_request_started',details={'turn':index})
        timing.record('provider_first_token',state='NOT_RECORDED',
                      cause='planner_request_started',details={'turn':index})
        args=[sys.executable,str(HERE/'model_pair_runner_v1.py'),r'C:\Program Files\nodejs\node.exe',
              str(Path.home()/'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),str(image),str(prompt_path),str(REPO),str(model_dir)]
        m=subprocess.run(args,capture_output=True,timeout=90)
        ended=time.perf_counter_ns()
        timing.record('planner_proposal_received',timestamp_ns=ended,
                      cause='planner_request_started',details={'turn':index})
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
            if proposal['road_visible'] is not True:
                raise ValueError('visual verification proposal does not see road')
            dump(root/'visual-verdict.json',proposal)
            dump(root/f'proposal-{index}.json',{'finish':True,'reason':'typed model requested independent verification'})
            published=time.perf_counter_ns()
            timing.record('verification_request_published',timestamp_ns=published,
                          cause='planner_proposal_received',details={'turn':index})
            result=wait_file(root/'result.json',30);completed=time.perf_counter_ns();code=driver.wait(timeout=10)
            evaluation=next(e for e in read(root/'finish.json')['reply']['records'] if e['event']=='independent_evaluation')
            assert code==0 and result['exit_code']==0 and evaluation['contract_satisfied'] is True
            final_event=timing.record('semantic_completion_detected',timestamp_ns=completed,
                        uncertainty_ns=25_000_000,cause='verification_request_published',
                        details={'turn':index,'definition':'successful independent evaluation file detected'})
            whole=interval(initial_event,final_event)
            dump(control/'result.json',{'exit_code':code,'success':True,'model_turns':len(turns),'started_ns':started,'finished_ns':time.perf_counter_ns(),
                                      'initial_observation_to_semantic_completion':whole,
                                      'scope':'fresh bounded OpenTTD timing envelope; independent guarded road score; no matched speed claim'})
            print(json.dumps({'success':True,'model_turns':len(turns)}),flush=True);break
        dump(root/f'proposal-{index}.json',{'steps':proposal['steps'],'rationale':proposal['rationale']})
        row['proposal_published_ns']=time.perf_counter_ns()
        timing.record('proposal_published',timestamp_ns=row['proposal_published_ns'],
                      cause='planner_proposal_received',details={'turn':index})
        applied=wait_file(root/f'applied-{index}.json',30);row['applied_read_ns']=time.perf_counter_ns()
        timing.record('first_useful_feedback_detected',timestamp_ns=row['applied_read_ns'],
                      uncertainty_ns=25_000_000,cause='proposal_published',
                      details={'turn':index,'definition':'fresh observation plus typed terminal detected'})
        dump(control/'turns.json',turns)
        observation=applied['result']['state']['continuation']['observation']
        previous={'proposal':proposal,'resolution':applied['result']['state']['last_resolution']}
        print(json.dumps({'turn':index,'kind':'act','status':previous['resolution']['terminal']['status'],'sequence':observation['sequence']}),flush=True)
    else:raise RuntimeError('bounded turn limit; no automatic success')
except Exception as error:
    dump(control/'error.json',{'type':type(error).__name__,'detail':str(error),'automatic_retry':False});raise
finally:
    if driver.poll() is None:
        if root.exists():dump(root/'abort.json',{'finish':True,'reason':'supervisor failure cleanup; no success claim'})
        try:driver.wait(timeout=15)
        except subprocess.TimeoutExpired:driver.terminate();driver.wait(timeout=10)
    timing.close()
