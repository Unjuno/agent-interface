"""Windows supervisor for one bounded actual OpenTTD L-road model/action loop."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from PIL import Image
from openttd_proposal_schema_v5 import parse
from openttd_contact_sheet_v1 import build as build_contact_sheet
from timing_envelope_v1 import interval
from timing_envelope_v2 import Recorder
HERE=Path(__file__).resolve().parent;REPO=HERE.parent.parent
arm=sys.argv[1]
if arm!='fixed-astra':raise SystemExit('arm must be fixed-astra')
base=HERE/'results/timing-envelope-openttd-l-01';root=base/arm;control=base/(arm+'-control');control.mkdir(parents=True,exist_ok=False)
def dump(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path)
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def linux(path):
    path=path.resolve();return '/mnt/'+path.drive[0].lower()+path.as_posix()[2:]
plan={'scope':'fresh seed-991003 OpenTTD five-tile L objective with buffered process-scoped timing envelope','arm':arm,
      'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['timing_envelope_openttd_l_supervisor_v1.py','timing_envelope_openttd_l_driver_v1.py','timing_envelope_v1.py','timing_envelope_v2.py','openttd_proposal_schema_v5.py','openttd_finish_outcome_v1.py','model_pair_runner_v2.py','session_v22.py','openttd_contact_sheet_v1.py']},
      'max_turns':12,'seed_semantics':'byte-pinned seed-991003 save; target tiles 977,978,979,1043,1107; closed toolbar',
      'model_route':'all gpt-6-astra medium','prompt_policy':'batched hover contact sheet, exact road target guard and ambiguity escalation','initial_ui_state':'closed toolbar; signs A, B corner, C and X keep clear'}
dump(control/'plan.json',plan);timing=Recorder(control/'timing-envelope.jsonl');started=time.perf_counter_ns();timing.record('supervisor_started',timestamp_ns=started);timing.record('runtime_receipt',state='NOT_RECORDED',cause='supervisor_started');timing.record('os_injection',state='NOT_RECORDED',cause='runtime_receipt');turns=[]
driver=subprocess.Popen(['wsl','-d','Ubuntu','--','python3',linux(HERE/'timing_envelope_openttd_l_driver_v1.py'),arm],stdout=(control/'driver-stdout.txt').open('wb'),stderr=(control/'driver-stderr.txt').open('wb'))
def wait_file(path,seconds=120):
    deadline=time.monotonic()+seconds
    while not path.exists():
        if driver.poll() is not None:raise RuntimeError('driver exited before '+path.name)
        if time.monotonic()>deadline:raise TimeoutError(path.name)
        time.sleep(.025)
    return read(path)
def wait_outcome(paths,seconds=30):
    deadline=time.monotonic()+seconds
    while True:
        for path in paths:
            if path.exists():return path,read(path)
        if driver.poll() is not None:raise RuntimeError('driver exited before a persisted outcome')
        if time.monotonic()>deadline:raise TimeoutError('persisted outcome')
        time.sleep(.025)
try:
    ready=wait_file(root/'ready.json');initial_detected=time.perf_counter_ns();initial_event=timing.record('initial_observation_detected',timestamp_ns=initial_detected,uncertainty_ns=25_000_000,cause='supervisor_started',details={'definition':'ready.json first detected by 25ms file poll'})
    task=ready['task'];observation=ready['observation'];previous=None;planner_image=None;exploration_history=[]
    for index in range(1,13):
        image=root/'runtime'/Path(observation['image']).name
        with Image.open(image) as opened:image_dimensions=[opened.width,opened.height]
        presented_image=planner_image or image
        with Image.open(presented_image) as opened:presentation_dimensions=[opened.width,opened.height]
        app_geometry=observation['pointer_binding']['geometry']
        prompt=f'''You control an isolated OpenTTD road fixture using its current screenshot. Task: {task} Choose the next bounded visual action. Use the road-construction toolbar and straight-road tool when visible. This objective requires two connected directional segments sharing the B corner; do not treat one straight segment as completion. Treat tooltip purpose and target noun as an action guard: Display/list is a status window, and Build tramways is not Build roads. Do not click either for this task. Continue until visible controls specifically indicate road construction or Build roads. If toolbar meanings are uncertain, inspect up to three distinct icons in one act using repeated pointer_move + dwell_observe pairs around 800ms. Spread probes across unexplored toolbar regions. The next planner image preserves intermediate tooltips as labeled strips. Do not revisit an inspected coordinate within about 12 pixels unless visible state changed. Close an irrelevant window through its visible close control. A prior needs_decision/focus_changed or zero steps_completed does not mean the application effect failed: inspect the screenshot and never blindly replay.
Return ONLY one JSON object of exactly one form:
{{"kind":"act","steps":[...],"rationale":"short explanation"}}
{{"kind":"verify","road_visible":BOOLEAN,"rationale":"short explanation"}}
{{"kind":"stop","rationale":"why no justified next action is available"}}
Use verify only when both A-to-B and B-to-C road segments are visibly complete and the X area remains clear; it requests the independent engine guard score. Rationale 1..600 characters. Act has 1..6 steps. Supported exact step shapes:
{{"op":"pointer_move","x":INTEGER,"y":INTEGER}}
{{"op":"dwell_observe","delay_ms":100..2000}}
{{"op":"pointer_click","x":INTEGER,"y":INTEGER}}
{{"op":"pointer_drag","points":[{{"x":INTEGER,"y":INTEGER}},...],"duration_ms":80..1000}}
{{"op":"observe"}}
Coordinates are absolute in the original full screenshot. Original screenshot dimensions: {image_dimensions}. Presented dimensions: {presentation_dimensions}. If taller, its first {image_dimensions[1]} rows are current and lower strips are prior hover tooltips. Active app geometry [left,top,width,height]: {app_geometry}. Valid bounds x0..{image_dimensions[0]-1},y0..{image_dimensions[1]-1}; remain inside the active app. No extra fields, keys, tools or shell. The harness obtains a fresh observation and checks unchanged focus/binding before input. Propose only actions justified by the current image.
Current observation sequence: {observation['sequence']}.
Previous proposal and runtime outcome: {json.dumps(previous,ensure_ascii=True)}
Hover exploration history: {json.dumps(exploration_history,ensure_ascii=True)}
'''
        prompt_path=root/f'prompt-{index}.txt';prompt_path.write_text(prompt,encoding='utf-8');model_dir=root/f'model-{index}';begin=time.perf_counter_ns();timing.record('planner_request_started',timestamp_ns=begin,cause='initial_observation_detected' if index==1 else 'first_useful_feedback_detected',details={'turn':index,'image_sequence':observation['sequence']});timing.record('provider_request_received',state='NOT_RECORDED',cause='planner_request_started',details={'turn':index});timing.record('provider_first_token',state='NOT_RECORDED',cause='planner_request_started',details={'turn':index})
        args=[sys.executable,str(HERE/'model_pair_runner_v2.py'),r'C:\Program Files\nodejs\node.exe',str(Path.home()/'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),str(presented_image),str(prompt_path),str(REPO),str(model_dir),'gpt-6-astra','medium']
        model_run=subprocess.run(args,capture_output=True,timeout=90);ended=time.perf_counter_ns();timing.record('planner_proposal_received',timestamp_ns=ended,cause='planner_request_started',details={'turn':index});(control/f'model-{index}-stdout.txt').write_bytes(model_run.stdout);(control/f'model-{index}-stderr.txt').write_bytes(model_run.stderr)
        if model_run.returncode!=0:raise RuntimeError('model runner failed; no retry')
        records=[json.loads(line) for line in (model_dir/'events.jsonl').read_text(encoding='utf-8').splitlines()];items=[e['item'] for e in records if e.get('type')=='item.completed']
        if len(items)!=1 or items[0].get('type')!='agent_message':raise ValueError('one model proposal required')
        proposal=parse(items[0]['text']);dump(root/f'typed-{index}.json',proposal);row={'turn':index,'model_runner_started_ns':begin,'model_runner_returned_ns':ended,'kind':proposal['kind'],'requested_model':'gpt-6-astra','requested_effort':'medium'};turns.append(row);dump(control/'turns.json',turns)
        if proposal['kind']=='stop':raise RuntimeError('model stopped: '+proposal['rationale'])
        if proposal['kind']=='verify':
            if proposal['road_visible'] is not True:raise ValueError('visual verification proposal does not see road')
            dump(root/'visual-verdict.json',proposal);dump(root/f'proposal-{index}.json',{'finish':True,'reason':'typed model requested independent verification'});published=time.perf_counter_ns();timing.record('verification_request_published',timestamp_ns=published,cause='planner_proposal_received',details={'turn':index})
            outcome_path,result=wait_outcome([root/'result.json',root/'failure-evaluation.json'],30);completed=time.perf_counter_ns();code=driver.wait(timeout=10);evaluation=next(e for e in read(root/'finish.json')['reply']['records'] if e['event']=='independent_evaluation');assert code==0
            if outcome_path.name=='failure-evaluation.json':
                assert result['success'] is False and evaluation['success'] is False;dump(control/'failure-result.json',{'exit_code':code,'success':False,'arm':arm,'model_turns':len(turns),'failure_mode':result['failure_mode'],'scope':'visual verification rejected by independent L-road score'});raise RuntimeError('independent task score rejected visual verification; failure retained')
            assert evaluation['success'] is True;final_event=timing.record('semantic_completion_detected',timestamp_ns=completed,uncertainty_ns=25_000_000,cause='verification_request_published',details={'turn':index,'definition':'successful independent evaluation file detected'});whole=interval(initial_event,final_event);dump(control/'result.json',{'exit_code':code,'success':True,'arm':arm,'model_turns':len(turns),'started_ns':started,'finished_ns':time.perf_counter_ns(),'initial_observation_to_semantic_completion':whole,'scope':'fresh bounded OpenTTD L timing envelope; independent guarded score'});print(json.dumps({'success':True,'model_turns':len(turns)}),flush=True);break
        dump(root/f'proposal-{index}.json',{'steps':proposal['steps'],'rationale':proposal['rationale']});moves=[[step['x'],step['y']] for step in proposal['steps'] if step.get('op')=='pointer_move']
        if moves:exploration_history.append({'turn':index,'points':moves,'rationale':proposal['rationale']})
        row['proposal_published_ns']=time.perf_counter_ns();timing.record('proposal_published',timestamp_ns=row['proposal_published_ns'],cause='planner_proposal_received',details={'turn':index});applied=wait_file(root/f'applied-{index}.json',30);row['applied_read_ns']=time.perf_counter_ns();timing.record('first_useful_feedback_detected',timestamp_ns=row['applied_read_ns'],uncertainty_ns=25_000_000,cause='proposal_published',details={'turn':index,'definition':'fresh observation plus typed terminal detected'});dump(control/'turns.json',turns)
        observation=applied['result']['state']['continuation']['observation'];current_image=root/'runtime'/Path(observation['image']).name;planner_image=build_contact_sheet(current_image,applied,proposal,root/'runtime',root/f'planner-{index+1}.png');previous={'proposal':proposal,'resolution':applied['result']['state']['last_resolution']};print(json.dumps({'turn':index,'kind':'act','status':previous['resolution']['terminal']['status'],'sequence':observation['sequence']}),flush=True)
    else:
        dump(root/'abort.json',{'finish':True,'reason':'bounded turn limit; independent failure score required'});failure=wait_file(root/'failure-evaluation.json',30);driver.wait(timeout=10);assert failure['success'] is False;raise RuntimeError('bounded turn limit; independent failure retained')
except Exception as error:
    dump(control/'error.json',{'type':type(error).__name__,'detail':str(error),'automatic_retry':False});raise
finally:
    if driver.poll() is None:
        if root.exists():dump(root/'abort.json',{'finish':True,'reason':'supervisor failure cleanup; no success claim'})
        try:driver.wait(timeout=15)
        except subprocess.TimeoutExpired:driver.terminate();driver.wait(timeout=10)
    timing.close()
