"""Saved-only paired custody reconstruction; no producer/native/process imports.

Cooperative local records are evidence, not OS/server/hardware authentication.
Missing historical decision clocks remain INCOMPLETE, never retroactive PASS.
"""
import base64
from collections import Counter
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys

from PIL import Image
from file_audit import score_arm


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return (json.dumps(value, sort_keys=True)+'\n').encode()


def positive(value):
    return type(value) is int and value > 0


def mapped(root, name, prefix):
    path = PurePosixPath(name)
    check(type(name) is str and path.is_absolute() and '..' not in path.parts
          and str(path).startswith(prefix+'/'), 'PATH_MAPPING_INVALID')
    return root.joinpath(*path.relative_to(prefix).parts)


def sealed(directory, filename='payload.bin'):
    directory = Path(directory)
    marker_blob = (directory/'ready.json').read_bytes()
    check(marker_blob.endswith(b'\n'), 'SEALED_MARKER_INCOMPLETE')
    marker = json.loads(marker_blob)
    check(type(marker) is dict and set(marker)=={'bytes','sha256'}
          and type(marker['bytes']) is int and marker['bytes']>=0, 'SEALED_MARKER_SCHEMA')
    blob = (directory/filename).read_bytes()
    check(len(blob)==marker['bytes'] and digest(blob)==marker['sha256'],'SEALED_PAYLOAD_CHANGED')
    return blob


def original_response(stdout):
    events = [json.loads(line) for line in stdout.decode().splitlines() if line]
    check(all(type(event) is dict and type(event.get('type')) is str for event in events),
          'PROCESS_EVENT_SCHEMA')
    threads, messages, turns = [], [], []
    for event in events:
        kind = event['type']
        check(kind not in ('error','turn.failed'),'PROCESS_FAILED_EVENT')
        if kind=='thread.started':
            threads.append(event.get('thread_id'))
        if kind.startswith('item.'):
            item = event.get('item')
            check(type(item) is dict and item.get('type') in ('agent_message','reasoning'),
                  'PROCESS_TOOL_EVENT')
            if kind=='item.completed' and item['type']=='agent_message':
                messages.append(item.get('text'))
        if kind=='turn.completed':
            turns.append(event.get('usage'))
    check(len(threads)==len(messages)==len(turns)==1 and type(threads[0]) is str
          and bool(threads[0]) and type(messages[0]) is str,'PROCESS_COMPLETION_CARDINALITY')
    usage = turns[0]
    required = {'input_tokens','cached_input_tokens','output_tokens'}
    check(type(usage) is dict and required<=set(usage)<=required|{'cache_write_input_tokens','reasoning_output_tokens'}
          and all(type(v) is int and v>=0 for v in usage.values())
          and usage['cached_input_tokens']<=usage['input_tokens'],'PROCESS_USAGE_INVALID')
    answer = json.loads(messages[0])
    check(type(answer) is dict and set(answer)=={'decision','observed_target','observed_decoy','prefix'}
          and all(type(v) is str for v in answer.values())
          and answer['decision'] in ('INSERT_PREFIX','NO_REPAIR','REFUSE')
          and (len(answer['prefix'])==1 if answer['decision']=='INSERT_PREFIX' else answer['prefix']==''),
          'PROCESS_ANSWER_SCHEMA')
    return dict(answer=answer,usage=usage,call_id=threads[0])


def outer_capture(directory):
    attempt, receipt = read(directory/'attempt.json'), read(directory/'receipt.json')
    check(all(receipt.get(k)==v for k,v in attempt.items()),'OUTER_PROCESS_ATTEMPT_JOIN')
    check(receipt.get('exit_code')==0 and receipt.get('launch_error') is None,'OUTER_PROCESS_FAILED')
    for name in ('attempt.json','stdout.bin','stderr.bin'):
        check(digest((directory/name).read_bytes())==receipt['output_sha256'][name],
              'OUTER_PROCESS_BYTES_CHANGED')
    check(datetime.fromisoformat(receipt['started_utc'])<=datetime.fromisoformat(receipt['finished_utc']),
          'OUTER_PROCESS_CLOCK')
    return receipt


def exchange_call(root, slot, plan, host, nonces):
    directory = root/'exchange'/slot
    request = json.loads(sealed(directory/'request'))
    image, prompt = sealed(directory/'image','payload.png'), sealed(directory/'prompt')
    check(request['slot']==slot and request['allocation']==plan['allocation']
          and request['freeze_sha256']==digest((root/'plan.json').read_bytes())
          and request['image_sha256']==digest(image) and request['prompt_sha256']==digest(prompt)
          and type(request['nonce']) is str and bool(request['nonce'])
          and request['nonce'] not in nonces, 'PROCESS_REQUEST_BINDING')
    nonces.add(request['nonce'])
    custody = root/'host'/slot
    attempt, receipt, reply = [read(custody/name) for name in ('attempt.json','receipt.json','reply.json')]
    frozen = host['plans'][slot]
    check(attempt['request']==request and attempt['argv']==frozen['argv']
          and attempt['timeout_seconds']==frozen['timeout_seconds'],'PROCESS_TRUSTED_ARGV_JOIN')
    check(all(receipt.get(k)==v for k,v in attempt.items()) and receipt['exit_code']==0
          and receipt['timed_out'] is False and receipt['launch_error'] is None,'PROCESS_RECEIPT_FAILED')
    check(datetime.fromisoformat(receipt['started_utc'])<=datetime.fromisoformat(receipt['finished_utc']),
          'PROCESS_CLOCK_INVALID')
    for name in ('stdout.bin','stderr.bin','attempt.json'):
        check(digest((custody/name).read_bytes())==receipt['output_sha256'][name],'PROCESS_ORIGINAL_BYTES_CHANGED')
    stdout, stderr = [(custody/name).read_bytes() for name in ('stdout.bin','stderr.bin')]
    parsed = original_response(stdout)
    check(reply['request']==request and reply['process']==receipt and reply['parsed']==parsed
          and reply['status']=='returned' and reply['error'] is None
          and reply['authority_granted'] is False and reply['replay_allowed'] is False,'PROCESS_REPLY_JOIN')
    envelope_blob = sealed(directory/'response')
    envelope = json.loads(envelope_blob)
    check(envelope['status']=='returned' and envelope['error'] is None and envelope['reply']==reply
          and base64.b64decode(envelope['stdout_base64'],validate=True)==stdout
          and base64.b64decode(envelope['stderr_base64'],validate=True)==stderr,'PROCESS_ENVELOPE_JOIN')
    expected = dict(image_sha256=digest(image),prompt_sha256=digest(prompt),
                    schema_sha256=frozen['schema_sha256'],executable_sha256=host['executable_sha256'],
                    argv_sha256=digest(canonical(frozen['argv'])))
    check(envelope['joins']==dict(before=expected,after=expected),'PROCESS_EXECUTED_ARTIFACT_JOIN')
    argv = frozen['argv']
    for flag in ('--image','--output-schema'):
        check(argv.count(flag)==1 and argv.index(flag)<len(argv)-1,'PROCESS_ARGV_ARTIFACT_SCHEMA')
    check(argv[argv.index('--image')+1].replace('\\','/')==
          host['directory'].replace('\\','/')+'/'+slot+'/image/payload.png','PROCESS_IMAGE_PATH_JOIN')
    client = json.loads(sealed(directory/'client-receipt'))
    check(client['reply']==reply and client['status']=='returned' and client['error'] is None
          and client['joins']==envelope['joins'] and client['response_sha256']==digest(envelope_blob)
          and client['stdout_sha256']==digest(stdout) and client['stderr_sha256']==digest(stderr)
          and positive(client['response_seen_ns']) and client['authority_granted'] is False
          and client['task_complete'] is False,'PROCESS_CLIENT_RECEIPT_JOIN')
    return dict(client=client,parsed=parsed,image=image,prompt=prompt)


def capture(root, arm, purpose, ready):
    source = read(arm/(purpose+'-capture.json'))
    native = source['native']
    artifact = native['artifact']
    blob = (arm/(purpose+'.png')).read_bytes()
    original = mapped(root,artifact['path'],'/out').read_bytes()
    check(digest(original)==artifact['sha256'] and len(original)==artifact['bytes'], 'IMAGE_NATIVE_ARTIFACT_JOIN')
    with Image.open(io.BytesIO(blob)) as image:
        check(image.mode=='RGB' and image.size==(native['width'],native['height']),'IMAGE_CAPTURE_SHAPE')
        pixels = image.tobytes()
    with Image.open(io.BytesIO(original)) as image:
        check(image.convert('RGB').tobytes()==pixels,'IMAGE_CAPTURE_PIXEL_JOIN')
    # Native raw X11 BGRX/XRGB includes a discarded padding byte. PNG RGB
    # cannot reconstruct its hash. Verify retained original PNG pixels and
    # the cooperative frozen writer's raw-hash metadata join, not fake RGB=raw.
    check(native['sha256']==artifact['source_raw_sha256']
          and native['bytes']==native['width']*native['height']*4
          and native['native_window_id']==ready['root']['id']
          and source['pointer_binding']['surface']==ready['root']['id']
          and source['capture_ns']==native['capture_started_ns']
          and native['capture_started_ns']<=native['capture_ended_ns'],'IMAGE_CAPTURE_SOURCE_JOIN')
    return source,blob


def app_trace(directory, freeze):
    ready, app = read(directory/'ready.json'),read(directory/'app_result.json')
    check(positive(ready['pid']) and type(ready['token']) is str and bool(ready['token'])
          and ready['freeze_sha256']==freeze,'APP_READY_BINDING')
    binding = dict(pid=ready['pid'],token=ready['token'],root_id=ready['root']['id'],
                   target_id=ready['target']['id'],freeze_sha256=freeze)
    check(all(positive(binding[k]) for k in ('root_id','target_id')),'APP_SURFACE_BINDING')
    check(app['pid']==ready['pid'] and app['token']==ready['token']
          and app['started_ns']<ready['ready_ns']<app['ended_ns'],'APP_LIFETIME_BINDING')
    requests = sorted(directory.glob('request-*.json'))
    check(len(requests)==len(list(directory.glob('reply-*.json'))),'APP_REPLY_CARDINALITY')
    nonces, snapshots = set(),{}
    for index,path in enumerate(requests,1):
        check(path.name==f'request-{index:06d}.json','APP_REQUEST_SEQUENCE')
        request, reply = read(path),read(directory/f'reply-{index:06d}.json')
        check(request['token']==ready['token'] and request['nonce'] not in nonces
              and reply['status']=='returned' and reply['nonce']==request['nonce'],'APP_REPLY_NONCE_JOIN')
        nonces.add(request['nonce'])
        if request['operation']=='snapshot':
            current = reply['snapshot']
            check(current['binding']==binding and current['nonce']==request['nonce']
                  and current['sequence']==len(snapshots)+1
                  and app['started_ns']<=current['started_ns']<=current['completed_ns']<=app['ended_ns'],
                  'APP_SNAPSHOT_BINDING')
            snapshots[current['nonce']]=current
        else:
            check(request['operation'] in ('drift','finish'),'APP_REQUEST_OPERATION')
    check(app['snapshot_count']==len(snapshots),'APP_SNAPSHOT_COUNT_JOIN')
    return ready,app,binding,snapshots


def qualification(current, binding, nonce, minimum, boundary, checked, age):
    check(type(current) is dict and current['binding']==binding and current['nonce']==nonce,
          'SNAPSHOT_IDENTITY_JOIN')
    check(all(positive(v) for v in (minimum,boundary,checked,current['sequence'],
                                  current['started_ns'],current['completed_ns']))
          and age==50_000_000,'DECISION_CLOCK_SCHEMA')
    if current['sequence']<=minimum:
        return 'SNAPSHOT_NOT_NEW'
    if not boundary<current['started_ns']<=current['completed_ns']<=checked:
        return 'SNAPSHOT_CLOCK'
    if checked-current['started_ns']>age:
        return 'SNAPSHOT_EXPIRED'
    return None if current['focus']=='target' else 'FOCUS_NOT_TARGET'


def semantic_reason(answer,current,wanted):
    if answer['observed_target']!=current['target'] or answer['observed_decoy']!=current['decoy']:
        return 'MODEL_STATE_MISMATCH'
    if answer['decision']=='REFUSE':
        return 'MODEL_REFUSED'
    if current['decoy']:
        return 'DECOY_NOT_EMPTY'
    if answer['decision']=='NO_REPAIR':
        return 'CURRENT_TASK_EXACT' if current['target']==wanted else 'TASK_NOT_EXACT'
    return ('CURRENT_PREFIX_REPAIR' if current['target'] and answer['prefix']+current['target']==wanted
            else 'PREFIX_NOT_TASK_REPAIR')


def native_report(report, raw_results):
    result = report['result']
    check(report['task_success'] is None and report['replay_allowed'] is False,'NATIVE_REPORT_AUTHORITY')
    check(report.get('status')==result.get('status'),'NATIVE_OUTER_STATUS_JOIN')
    check(any(result==raw for raw in raw_results),'NATIVE_ORIGINAL_RESULT_JOIN')
    if result.get('status')=='refused' and result.get('input_dispatched') is False:
        check('execution' not in result,'NATIVE_REFUSAL_EXECUTION_CONTRADICTION')
        return None
    execution = result.get('execution',{})
    check(positive(execution.get('started_ns')) and execution['started_ns']<=execution['ended_ns'],
          'NATIVE_EXECUTION_CLOCK')
    releases = execution.get('releases',[])
    check(bool(releases) and all(value.get('verified') is True and value.get('keys_down')==[]
          and value.get('buttons_down')==[] and execution['started_ns']<=value['monotonic_ns']<=execution['ended_ns']
          for value in releases),'NATIVE_RELEASE_NOT_EMPTY')
    return execution


def native_completed(report):
    result=report['result']
    check(report.get('status')==result.get('status'),'NATIVE_OUTER_STATUS_JOIN')
    execution=result.get('execution')
    return (report.get('status')=='completed' and type(execution) is dict
            and bool(execution.get('releases'))
            and all(value.get('verified') is True and value.get('keys_down')==[]
                    and value.get('buttons_down')==[] for value in execution['releases']))


def control_prefix_transition(control, answer):
    if answer['decision']!='INSERT_PREFIX':
        return
    calls=control['native_calls']
    if len(calls)==1:
        check(calls[0]['tail']==[dict(op='key_chord',keys=['Home']),
                                 dict(op='text',text=answer['prefix'])]
              and not native_completed(calls[0]['report']),
              'CONTROL_PREFIX_INCOMPLETE_OUTCOME')
    elif len(calls)==2:
        check(calls[0]['tail']==[dict(op='key_chord',keys=['Home']),
                                 dict(op='text',text=answer['prefix'])]
              and native_completed(calls[0]['report']),
              'CONTROL_PREFIX_BEFORE_SAVE_COMPLETION')


def native_program(report, directory, *, tail=None, click_target=None, gaps=None):
    result = report['result']
    if result.get('input_dispatched') is False:
        return None
    matches = []
    for path in directory.glob('guarded-session-*/program-guarded-*.json'):
        program = read(path)
        dispatch = read(path.parent/('public-dispatch-'+program['program_id']+'.json'))
        if all(result.get(key)==value for key,value in dispatch.get('result',{}).items()):
            matches.append((path,program,dispatch))
    check(len(matches)==1,'NATIVE_PROGRAM_DISPATCH_JOIN')
    path,program,dispatch = matches[0]
    check(dispatch['status']=='returned' and program['terminal']==dict(release_all_required=True)
          and program['schema']=='agent-interface/program-v1','NATIVE_PROGRAM_SCHEMA')
    ops = program['ops']
    if tail is not None:
        check(ops==[dict(op='focus',target='app'),*tail,dict(op='release_all')],
              'NATIVE_PROGRAM_MODEL_INTENT_CHANGED')
    else:
        check(click_target is not None and ops==[dict(op='focus',target='app'),
            dict(op='pointer_move',frame='screen_physical_px',x=click_target['x']+16,
                 y=click_target['y']+click_target['height']//2),
            dict(op='pointer_button',button='left',down=True),
            dict(op='pointer_button',button='left',down=False),dict(op='release_all')],
            'NATIVE_PROGRAM_FOCUS_CLICK_CHANGED')
    checks = result.get('guard_checks',[])
    check(bool(checks) and program['source']['observation_seq']==checks[0]['observation_sequence'],
          'NATIVE_PROGRAM_SOURCE_JOIN')
    additional = result.get('additional_input_checks',[])
    if additional:
        check(program['source']['binding_revision']==additional[0]['binding_revision']
              and program['authority']['lease_id']=='native-x11-'+additional[0]['scope'].removeprefix('native-x11:'),
              'NATIVE_PROGRAM_BINDING_JOIN')
    completed = result['execution']['completed_ops']
    check(type(completed) is list and all(type(index) is int and 0<=index<len(ops) for index in completed)
          and completed==sorted(set(completed)),'NATIVE_PROGRAM_COMPLETED_OPS')
    if result['status']=='completed':
        check(completed==list(range(len(ops))),'NATIVE_PROGRAM_INCOMPLETE_SUCCESS')
    expiry=program['authority']['expires_at_ns']
    check(positive(expiry),'NATIVE_PROGRAM_LEASE_EXPIRY_SCHEMA')
    check(result['execution']['started_ns']<expiry,'NATIVE_PROGRAM_TASK_AFTER_LEASE_EXPIRY')
    if result['status']=='completed':
        check(expiry>=result['execution']['ended_ns'],'NATIVE_PROGRAM_LEASE_EXPIRED')
    elif result['execution']['ended_ns']>expiry:
        check(any(value.get('verified') is True and value.get('monotonic_ns',0)>=expiry
                  for value in result['execution'].get('releases',[])),
              'NATIVE_PROGRAM_EXPIRY_CLEANUP_UNVERIFIED')
        if gaps is not None:
            gaps.append('NATIVE_LEASE_CROSSES_EXECUTION_WITHOUT_TASK_PHASE_TIMES')
    return path.name


def audit(root):
    root = Path(root)
    plan_blob = (root/'plan.json').read_bytes()
    plan, host = json.loads(plan_blob),read(root/'host-plan.json')
    freeze = digest(plan_blob)
    gaps, usage = [],Counter()
    check(plan['schema']=='a15-live-paired-study-v1' and 1<=len(plan['rows'])<=4,'PLAN_SCHEMA')
    ids = [row['id'] for row in plan['rows']]
    check(len(set(ids))==len(ids),'PLAN_ROW_DUPLICATE')
    slots = {name+'-'+kind for name in ids for kind in ('first','recovery')}
    check(set(host['plans'])==slots and host['allocation']==plan['allocation']
          and host['freeze_sha256']==freeze and sealed(root/'host/host-plan')==(root/'host-plan.json').read_bytes(),
          'HOST_PLAN_FREEZE_JOIN')
    for path,expected in plan['source_sha256'].items():
        check(digest(mapped(root/'source-capsule',path,'/src').read_bytes())==expected,'SOURCE_CAPSULE_CHANGED')
    attempt, outcome = read(root/'candidate/study-attempt.json'),read(root/'candidate/study-result.json')
    check(attempt['plan']==plan and attempt['freeze_sha256']==outcome['freeze_sha256']==freeze
          and attempt['allocation']==outcome['allocation']==plan['allocation']
          and outcome['error'] is None and outcome['uncovered_imports']==[]
          and [row['id'] for row in outcome['rows']]==ids,'SOURCE_STUDY_PLAN_JOIN')
    for imported in outcome['runtime_imports']+outcome.get('local_sources',[]):
        check(plan['source_sha256'].get(imported['path'])==imported['sha256'],'SOURCE_RUNTIME_UNCOVERED')
    runtime_names = [value['module'] for value in outcome['runtime_imports']]
    anchors = {'runtime.backends.x11_v1.backend','runtime.backends.x11_v1.capture_artifacts',
               'runtime.backends.x11_v1.session','runtime.cli_v1.mcp_guarded',
               'runtime.cli_v1.mcp_session','runtime.guarded_x11_v1.bridge','runtime.core_v1.compiled_gui'}
    check(len(runtime_names)==len(set(runtime_names)) and anchors<=set(runtime_names),
          'SOURCE_RUNTIME_ANCHOR_MISSING')
    if not outcome.get('local_sources'):
        gaps.append('SOURCE_LOCAL_FINAL_CLOSURE_MISSING')
    else:
        prefix = '/src/research/integration/tk_model_task_guard_5260_a15_wslc_20261004/'
        mandatory = {prefix+name for name in ('paired_study.py','live_pair.py','live_app.py','task_session.py',
            'task_guard.py','file_exchange.py','host_bridge.py','model_contract.py','construction_x11.py')}
        names = [value['path'] for value in outcome['local_sources']]
        check(len(names)==len(set(names)) and set(names)==mandatory,'SOURCE_LOCAL_CLOSURE_MEMBERSHIP')
    for role in ('host','candidate'):
        outer_capture(root/(role+'-launch'))
    schema = root/'response.schema.json'
    if not schema.exists():
        gaps.append('SOURCE_SCHEMA_BYTES_NOT_RETAINED')
    else:
        check(all(value['schema_sha256']==digest(schema.read_bytes()) for value in host['plans'].values()),
              'SOURCE_SCHEMA_BYTES_CHANGED')
    nonces, call_ids, rows, used_slots = set(),set(),[],set()
    quality = {arm:Counter() for arm in ('control','guard')}
    cli_calls = 0
    for schedule in plan['rows']:
        pair = root/'candidate'/schedule['id']
        first_slot, recovery_slot = [schedule['id']+'-'+kind for kind in ('first','recovery')]
        first = exchange_call(root,first_slot,plan,host,nonces)
        used_slots.add(first_slot)
        check(read(pair/'first-model.json')==first['client'],'FIRST_ORIGINAL_MODEL_JOIN')
        paired = read(pair/'paired-result.json')
        check(paired['first']==first['client'],'FIRST_PAIR_SUMMARY_REPLACED')
        answer, receipt_clock = first['parsed']['answer'],first['client']['response_seen_ns']
        initial = read(pair/'initial-pair.json')
        app_data, image_blobs, raw_by_arm, all_reports = {},{}, {}, {'control':[],'guard':[]}
        for arm in ('control','guard'):
            ready,app,binding,snapshots = app_trace(pair/arm/'app',freeze)
            app_data[arm]=(ready,app,binding,snapshots)
            check(app['started_ns']<receipt_clock<app['ended_ns'],'APP_NOT_LIVE_AT_FIRST_RESPONSE')
            source,blob = capture(root,pair/arm,'initial',ready)
            image_blobs[arm]=blob
            expected = initial['arms'][arm]
            check(expected['source']==source and expected['png_sha256']==digest(blob)
                  and snapshots.get(expected['snapshot']['nonce'])==expected['snapshot']
                  and expected['snapshot']['target']==schedule['target']
                  and expected['snapshot']['decoy']==schedule['decoy'],'IMAGE_INITIAL_STIMULUS_JOIN')
            raw_by_arm[arm]=[read(path) for path in (pair/arm/'native').glob('guarded-session-*/result-*.json')]
            scored = score_arm(pair/arm/'app',wanted=schedule['wanted'],initial_decoy=schedule['decoy'])
            quality[arm][scored['quality']]+=1
        check(image_blobs['control']==image_blobs['guard']==first['image']
              and initial['image_identical'] is True and first['prompt']==plan['prompt'].encode(),'IMAGE_PAIRED_FIRST_JOIN')
        check(app_data['control'][0]['pid']!=app_data['guard'][0]['pid']
              and app_data['control'][0]['token']!=app_data['guard'][0]['token'],'APP_PAIR_IDENTITY_COLLISION')
        check(read(pair/'close.json')['errors']==[],'APP_CLEANUP_FAILED')
        control = read(pair/'control-result.json')
        check(paired['control']==control,'CONTROL_RESULT_JOIN')
        for call in control['native_calls']:
            native_report(call['report'],raw_by_arm['control'])
            native_program(call['report'],pair/'control/native',tail=call['tail'],gaps=gaps)
            all_reports['control'].append(call['report'])
        check(not control['native_calls'] if answer['decision']=='REFUSE' else
              [call['tail'] for call in control['native_calls']]==
              ([list([dict(op='key_chord',keys=['Home']),dict(op='text',text=answer['prefix'])])]
               if answer['decision']=='INSERT_PREFIX' else [])+
              ([[dict(op='key_chord',keys=['CTRL','s'])]] if control['native_calls'] and
                control['native_calls'][-1]['tail']==[dict(op='key_chord',keys=['CTRL','s'])] else []),
              'CONTROL_MODEL_INTENT_CHANGED')
        if answer['decision']=='REFUSE':
            check(control['status']=='YIELD' and control['reason']=='MODEL_REFUSE'
                  and control['task_complete'] is False and control['grants_input_authority'] is False
                  and not control['native_calls'],'CONTROL_REFUSAL_OUTCOME')
        else:
            check(bool(control['native_calls']),'CONTROL_REQUIRED_OPERATION_MISSING')
        control_prefix_transition(control,answer)
        if answer['decision']=='INSERT_PREFIX' and len(control['native_calls'])==1:
            check(control['status']=='YIELD' and control['reason']=='CONTROL_PREFIX_NATIVE_INCOMPLETE',
                  'CONTROL_PREFIX_INCOMPLETE_OUTCOME')
        elif answer['decision']=='INSERT_PREFIX' and len(control['native_calls'])==2:
            save_call=control['native_calls'][1]
            save_done=native_completed(save_call['report'])
            check(save_call['tail']==[dict(op='key_chord',keys=['CTRL','s'])]
                  and control['status']==('SAVE_DISPATCHED' if save_done else 'YIELD')
                  and control['reason']==('INDEPENDENT_FILE_SCORE_STILL_REQUIRED' if save_done
                                          else 'CONTROL_NATIVE_INCOMPLETE'),
                  'CONTROL_SAVE_COMPLETION_OUTCOME')
        elif control['native_calls']:
            save_call=control['native_calls'][-1]
            save_done=native_completed(save_call['report'])
            check(save_call['tail']==[dict(op='key_chord',keys=['CTRL','s'])]
                  and control['status']==('SAVE_DISPATCHED' if save_done else 'YIELD')
                  and control['reason']==('INDEPENDENT_FILE_SCORE_STILL_REQUIRED' if save_done
                                          else 'CONTROL_NATIVE_INCOMPLETE'),
                  'CONTROL_SAVE_COMPLETION_OUTCOME')
        check(control['task_complete'] is False and control['grants_input_authority'] is False,
              'CONTROL_RESULT_AUTHORITY_INVARIANTS')
        guard_records = [read(path) for path in sorted(pair.glob('guard-result-*.json'))]
        check(bool(guard_records) and guard_records[0]['review']==answer
              and guard_records[0]['response_seen_ns']==receipt_clock
              and paired['guard_first']==guard_records[0]['result'],'GUARD_FIRST_MODEL_JOIN')
        recovery = None
        if paired['recovery'] is not None:
            check(guard_records[0]['result']['reason']=='MODEL_STATE_MISMATCH'
                  and guard_records[0]['result']['native_calls']==[],'GUARD_RECOVERY_CONTEXT')
            recovery = exchange_call(root,recovery_slot,plan,host,nonces)
            used_slots.add(recovery_slot)
            check(paired['recovery']==recovery['client']==read(pair/'recovery-model.json'),'GUARD_RECOVERY_RESPONSE_JOIN')
            source,blob = capture(root,pair/'guard','recovery',app_data['guard'][0])
            check(blob==recovery['image'] and source['capture_ns']>receipt_clock,'IMAGE_RECOVERY_CHANGED_EVIDENCE')
            check(recovery['prompt'].startswith(plan['prompt'].encode()+b'\nChanged-evidence recovery, not a retry:'),
                  'PROCESS_RECOVERY_PROMPT_JOIN')
            discrepancy = json.loads(recovery['prompt'].splitlines()[-1])
            check(discrepancy['first_answer']==answer and discrepancy['capture_source']==source
                  and discrepancy['current_app_snapshot']==app_data['guard'][3].get(discrepancy['recovery_nonce'])
                  and discrepancy['current_app_snapshot']['started_ns']>source['capture_ns'],
                  'PROCESS_RECOVERY_DISCREPANCY_JOIN')
            check(len(guard_records)==2 and guard_records[1]['review']==recovery['parsed']['answer']
                  and guard_records[1]['response_seen_ns']==recovery['client']['response_seen_ns'],
                  'GUARD_RECOVERY_ADMISSION_JOIN')
        else:
            directory = root/'exchange'/recovery_slot
            skipped_blob = sealed(directory/'skip')
            skipped = json.loads(skipped_blob)
            check(not (directory/'request').exists() and skipped['slot']==recovery_slot
                  and skipped['allocation']==plan['allocation'] and skipped['freeze_sha256']==freeze
                  and skipped['nonce'] not in nonces and skipped['first_response_sha256']==first['client']['response_sha256']
                  and sealed(root/'host'/(recovery_slot+'-skip'))==skipped_blob,'PROCESS_RECOVERY_SKIP_JOIN')
            nonces.add(skipped['nonce'])
            used_slots.add(recovery_slot)
        native_snapshots = [read(path) for path in sorted((pair/'guard/native').glob('snapshot-*.json'))]
        lookup = app_data['guard'][3]
        for record in native_snapshots:
            reply = record['reply']
            check(reply['status']=='returned' and lookup.get(reply['nonce'])==reply['snapshot']
                  and reply['snapshot']['completed_ns']<=record['received_ns'],'APP_NATIVE_SNAPSHOT_JOIN')
        reviews = [read(path) for path in (pair/'guard/native').glob('review-*.json')]
        check(len(reviews)==len(guard_records),'GUARD_REVIEW_COUNT')
        high_water = 0
        focus_prior_high_water = None
        focus_first_checked = None
        for index,record in enumerate(guard_records):
            matches = [value for value in reviews if value['review']==record['review']
                       and value['response_seen_ns']==record['response_seen_ns'] and value['plan']==record['plan']]
            check(len(matches)==1,'GUARD_REVIEW_CUSTODY_JOIN')
            review = matches[0]
            current = review['snapshot']
            check(lookup.get(current['nonce'])==current and record['response_seen_ns']<current['started_ns'],
                  'GUARD_NEW_CURRENT_SNAPSHOT')
            reason = None
            if 'checked_ns' not in review:
                gaps.append(schedule['id']+':DECISION_CLOCK_REVIEW_MISSING')
                reason = 'FOCUS_NOT_TARGET' if current['focus']!='target' else None
            else:
                image_baseline = (initial['arms']['guard']['snapshot']['sequence'] if index==0 or recovery is None
                                  else discrepancy['current_app_snapshot']['sequence'])
                check(review['image_sequence']==image_baseline
                      and review['minimum_sequence']==max(image_baseline,high_water),'SNAPSHOT_HIGH_WATER_REVIEW')
                reason = qualification(current,app_data['guard'][2],current['nonce'],review['minimum_sequence'],
                    review['response_seen_ns'],review['checked_ns'],review['maximum_age_ns'])
                if reason is None:
                    high_water=current['sequence']
            reason = reason or semantic_reason(record['review'],current,schedule['wanted'])
            check(record['plan']['reason']==reason,'GUARD_DECISION_RECONSTRUCTION')
            if record['plan']['status']=='YIELD':
                check(record['result']['native_calls']==[],'GUARD_YIELD_EMITTED_TASK_INPUT')
            expected_plan_status=('PLAN_SAVE' if reason=='CURRENT_TASK_EXACT' else
                                  'PLAN_PREFIX' if reason=='CURRENT_PREFIX_REPAIR' else 'YIELD')
            check(record['plan']['status']==expected_plan_status,'GUARD_PLAN_STATUS_RECONSTRUCTION')
            check(record['result']['task_complete'] is False
                  and record['result']['grants_input_authority'] is False,
                  'GUARD_RESULT_AUTHORITY_INVARIANTS')
            expected_result_reason=(reason if expected_plan_status=='YIELD' else None)
            if expected_plan_status=='YIELD':
                check(record['result']['status']=='YIELD' and record['result']['reason']==expected_result_reason
                      and not record['result']['native_calls'],'GUARD_YIELD_RESULT_RECONSTRUCTION')
            elif expected_plan_status=='PLAN_SAVE':
                direct_calls=record['result']['native_calls']
                check(len(direct_calls)==1 and direct_calls[0]['purpose']=='save'
                      and direct_calls[0]['tail']==[dict(op='key_chord',keys=['CTRL','s'])],
                      'GUARD_DIRECT_SAVE_CARDINALITY')
                done=native_completed(direct_calls[0]['report'])
                check(record['result']['status']==('SAVE_DISPATCHED' if done else 'YIELD')
                      and record['result']['reason']==('INDEPENDENT_FILE_SCORE_STILL_REQUIRED' if done
                          else 'SAVE_NATIVE_NOT_COMPLETED_AND_RELEASED'),
                      'GUARD_DIRECT_SAVE_OUTCOME')
            elif expected_plan_status=='PLAN_PREFIX':
                prefix_calls=[value for value in record['result']['native_calls'] if value['purpose']=='prefix']
                check(len(prefix_calls)==1 and record['result']['native_calls'][0] is prefix_calls[0],
                      'GUARD_PREFIX_REQUIRED_OPERATION')
            for call in record['result']['native_calls']:
                execution = native_report(call['report'],raw_by_arm['guard'])
                native_program(call['report'],pair/'guard/native',tail=call['tail'],gaps=gaps)
                all_reports['guard'].append(call['report'])
                check(execution is None or current['completed_ns']<=execution['started_ns']<=execution['ended_ns']<=call['finished_ns'],
                      'NATIVE_ADMISSION_CLOCK_JOIN')
                if execution is not None and 'checked_ns' in review:
                    check(review['checked_ns']<=execution['started_ns'],'NATIVE_REVIEW_DECISION_CLOCK')
                check(any(call==original for original in [read(path) for path in (pair/'guard/native').glob('call-[0-9]*.json')]),
                      'NATIVE_CALL_CUSTODY_JOIN')
                checks = call['checks']
                check(bool(checks),'NATIVE_CURRENT_CHECKS_MISSING')
                additional = call['report']['result']['additional_input_checks']
                check(len(checks)==len(additional),'NATIVE_ADDITIONAL_CHECK_COUNT')
                for constraint,original in zip(checks,additional):
                    snapshot = constraint['snapshot']
                    check(lookup.get(snapshot['nonce'])==snapshot and constraint['stage']==original['stage']
                          and constraint['native_sequence']==original['observation_sequence']
                          and original['authority_granted'] is False,'NATIVE_CURRENT_CHECK_JOIN')
                    if 'checked_ns' not in constraint:
                        gaps.append(schedule['id']+':DECISION_CLOCK_NATIVE_MISSING')
                    else:
                        check(constraint['minimum_sequence']==high_water,'SNAPSHOT_HIGH_WATER_NATIVE')
                        check(original['started_ns']<=constraint['boundary_ns']<snapshot['started_ns']
                              <=snapshot['completed_ns']<=constraint['checked_ns']<=original['ended_ns'],
                              'NATIVE_CALLBACK_CLOCK_JOIN')
                        error = qualification(snapshot,app_data['guard'][2],snapshot['nonce'],constraint['minimum_sequence'],
                            constraint['boundary_ns'],constraint['checked_ns'],constraint['maximum_age_ns'])
                        expected_text = record['plan'].get('prior_target') if call['purpose']=='prefix' else schedule['wanted']
                        if error is None and (snapshot['target']!=expected_text or snapshot['decoy']):
                            error='CURRENT_TASK_DEPENDENCY_CHANGED'
                        check(constraint['error']==error and original['eligible']==(error is None),
                              'NATIVE_CURRENT_CHECK_RECONSTRUCTION')
                        if error is None:
                            high_water=snapshot['sequence']
                    if constraint['error'] is None:
                        expected_text = record['plan'].get('prior_target') if call['purpose']=='prefix' else schedule['wanted']
                        check(snapshot['target']==expected_text and snapshot['decoy']=='','NATIVE_TASK_DEPENDENCY_CHANGED')
                if call['purpose']=='prefix':
                    check(call['tail']==[dict(op='key_chord',keys=['Home']),dict(op='text',text=record['review']['prefix'])],
                          'NATIVE_MODEL_PREFIX_REPLACED')
                    effects = [value['reply']['snapshot'] for value in native_snapshots if value['purpose']=='repair-effect']
                    validations = [read(path) for path in (pair/'guard/native').glob('effect-validation-*.json')]
                    prefix_complete=native_completed(call['report'])
                    if not prefix_complete:
                        check(record['result']['status']=='YIELD' and not effects and not validations
                              and record['result']['reason']=='PREFIX_NATIVE_NOT_COMPLETED_AND_RELEASED'
                              and not any(value['purpose']=='save' for value in record['result']['native_calls']),
                              'NATIVE_PREFIX_INCOMPLETE_OUTCOME')
                    else:
                        check(len(effects)==1 and effects[0]['started_ns']>call['finished_ns'],
                              'NATIVE_REPAIR_EFFECT_JOIN')
                    if prefix_complete and not validations:
                        gaps.append(schedule['id']+':DECISION_CLOCK_EFFECT_MISSING')
                    elif prefix_complete and validations:
                        check(len(validations)==1 and validations[0]['snapshot']==effects[0]
                              and validations[0]['proposal']==record['plan']
                              and validations[0]['action_finished_ns']==call['finished_ns'],'NATIVE_EFFECT_VALIDATION_JOIN')
                        value = validations[0]
                        check(value['minimum_sequence']==high_water,'SNAPSHOT_HIGH_WATER_EFFECT')
                        session_error=qualification(effects[0],app_data['guard'][2],value['request_nonce'],value['minimum_sequence'],
                            value['action_finished_ns'],value['checked_ns'],value['maximum_age_ns'])
                        effect_error=qualification(effects[0],app_data['guard'][2],value['request_nonce'],
                            record['plan']['baseline_sequence'],value['action_finished_ns'],value['checked_ns'],
                            value['maximum_age_ns'])
                        effect_status=('YIELD' if effect_error or effects[0]['target']!=record['plan']['expected_target']
                                       or effects[0]['decoy'] else 'PLAN_SAVE')
                        effect_reason=(effect_error or 'REPAIR_EFFECT_NOT_EXACT' if
                                       effect_status=='YIELD' else 'CURRENT_REPAIR_EFFECT_EXACT')
                        check(('snapshot_error' not in value or value['snapshot_error']==qualification(
                            effects[0],app_data['guard'][2],value['request_nonce'],value['minimum_sequence'],
                            value['action_finished_ns'],value['checked_ns'],value['maximum_age_ns']))
                            and value['save_plan']['status']==effect_status
                            and value['save_plan']['reason']==effect_reason
                            and record['result']['reason']==(session_error if session_error else
                                value['save_plan']['reason'] if effect_status!='PLAN_SAVE' else
                                'SAVE_NATIVE_NOT_COMPLETED_AND_RELEASED' if
                                record['result']['native_calls'][-1]['purpose']=='save' and
                                record['result']['native_calls'][-1]['report']['result']['status']!='completed'
                                else 'INDEPENDENT_FILE_SCORE_STILL_REQUIRED'),
                            'NATIVE_EFFECT_VALIDATION_CHANGED')
                        effect_accepted=session_error is None and effect_status=='PLAN_SAVE'
                        ordered_calls=record['result']['native_calls']
                        check((len(ordered_calls)==2 and ordered_calls[0]['purpose']=='prefix'
                               and ordered_calls[1]['purpose']=='save') if effect_accepted else
                              (len(ordered_calls)==1 and ordered_calls[0]['purpose']=='prefix'),
                              'NATIVE_REPAIR_EFFECT_AUTHORIZES_SAVE')
                        save_complete=(effect_accepted and native_completed(ordered_calls[-1]['report']))
                        expected_final_reason=(session_error or effect_reason if not effect_accepted else
                            'INDEPENDENT_FILE_SCORE_STILL_REQUIRED' if save_complete else
                            'SAVE_NATIVE_NOT_COMPLETED_AND_RELEASED')
                        check(record['result']['status']==('SAVE_DISPATCHED' if save_complete else 'YIELD')
                              and record['result']['reason']==expected_final_reason,
                              'NATIVE_REPAIR_FINAL_OUTCOME')
                        if session_error is None and effect_status=='PLAN_SAVE':
                            high_water=effects[0]['sequence']
                        saves = [value for value in record['result']['native_calls'] if value['purpose']=='save']
                        if saves and saves[0]['report']['result'].get('execution'):
                            check(value['checked_ns']<=saves[0]['report']['result']['execution']['started_ns'],
                                  'NATIVE_EFFECT_BEFORE_SAVE_CLOCK')
                elif call['purpose']=='save':
                    check(call['tail']==[dict(op='key_chord',keys=['CTRL','s'])],'NATIVE_SAVE_INTENT_CHANGED')
                    saved = app_data['guard'][1]['saves']
                    if saved:
                        # Native emission/release can return before Tk finishes
                        # processing Ctrl+S/fsync. Join the actual received Save
                        # key and app receipt, not an invented synchronous bound.
                        keys = [event for event in app_data['guard'][1]['events']
                                if event['kind']=='KeyPress' and event['keysym']=='s'
                                and event['widget']=='target' and event['state'] & 4]
                        check(execution is not None and len(saved)==1
                              and len(keys)==1 and execution['started_ns']<=keys[0]['ns']
                              <=saved[0]['started_ns']<=saved[0]['completed_ns']<=app_data['guard'][1]['ended_ns'],
                              'NATIVE_SAVE_CLOCK_JOIN')
                else:
                    raise ValueError('NATIVE_UNEXPECTED_TASK_OPERATION')
            if index==0:
                focus_prior_high_water=high_water
                focus_first_checked=review.get('checked_ns')
        focus_path = pair/'focus-recovery.json'
        if focus_path.exists():
            focus = read(focus_path)
            check(paired['focus_recovery']==focus and guard_records[0]['result']['reason']=='FOCUS_NOT_TARGET'
                  and recovery is None and schedule['focus_drift'] is True,'GUARD_FOCUS_CONTEXT')
            execution = native_report(focus['report'],raw_by_arm['guard'])
            native_program(focus['report'],pair/'guard/native',click_target=app_data['guard'][0]['target'],gaps=gaps)
            all_reports['guard'].append(focus['report'])
            click_complete=native_completed(focus['report'])
            if not click_complete:
                check(focus['report']['result']['status']!='completed'
                      and receipt_clock==focus['original_response_seen_ns']
                      and len(guard_records)==1
                      and paired['guard_final']['status']=='YIELD'
                      and paired['guard_final']['native_calls']==[]
                      and paired['guard_final']['reason']=='FOCUS_RECOVERY_NATIVE_INCOMPLETE',
                      'GUARD_FOCUS_NATIVE_INCOMPLETE_OUTCOME')
            else:
                check(receipt_clock==focus['original_response_seen_ns']
                      and execution['ended_ns']<=focus['click_finished_ns']
                      and len(guard_records)==2 and guard_records[1]['review']==answer
                      and guard_records[1]['response_seen_ns']==max(receipt_clock,focus['click_finished_ns']),
                      'GUARD_FOCUS_NEW_ACK_BOUNDARY')
            prerequisite = pair/'focus-prerequisite.json'
            if not prerequisite.exists():
                gaps.append(schedule['id']+':DECISION_CLOCK_FOCUS_MISSING')
            else:
                value = read(prerequisite)
                check(value['original_review']==answer
                      and lookup.get(value['request_nonce'])==value['snapshot']
                      and value['minimum_sequence']==max(initial['arms']['guard']['snapshot']['sequence'],
                                                          focus_prior_high_water or 0)
                      and value['boundary_ns']>receipt_clock
                      and focus_first_checked is not None and value['boundary_ns']>focus_first_checked
                      and (execution is None or value['checked_ns']<=execution['started_ns']),
                      'GUARD_FOCUS_PREREQUISITE_JOIN')
                error = qualification(value['snapshot'],app_data['guard'][2],value['request_nonce'],value['minimum_sequence'],
                    value['boundary_ns'],value['checked_ns'],value['maximum_age_ns'])
                semantic = (semantic_reason(answer,value['snapshot'],schedule['wanted']) in
                    ('CURRENT_TASK_EXACT','CURRENT_PREFIX_REPAIR'))
                check(value['semantic_consistent'] is semantic and value['snapshot_error']==error,
                      'GUARD_FOCUS_PREREQUISITE_RECONSTRUCTION')
                check(error in (None,'FOCUS_NOT_TARGET') and semantic,
                      'GUARD_FOCUS_NOT_SEMANTIC_ONLY')
        denied_path=pair/'focus-recovery-denied.json'
        if denied_path.exists():
            denied=read(denied_path)
            prerequisite=read(pair/'focus-prerequisite.json')
            error=qualification(prerequisite['snapshot'],app_data['guard'][2],prerequisite['request_nonce'],
                prerequisite['minimum_sequence'],prerequisite['boundary_ns'],prerequisite['checked_ns'],
                prerequisite['maximum_age_ns'])
            semantic=(semantic_reason(answer,prerequisite['snapshot'],schedule['wanted']) in
                      ('CURRENT_TASK_EXACT','CURRENT_PREFIX_REPAIR'))
            prerequisite_min=max(initial['arms']['guard']['snapshot']['sequence'],focus_prior_high_water or 0)
            original_app_snapshot=app_data['guard'][3].get(prerequisite['request_nonce'])
            denial_required=error not in (None,'FOCUS_NOT_TARGET') or not semantic
            expected_reason=('MIXED_SEMANTIC_FOCUS_YIELD' if not semantic else
                             'FOCUS_PREREQUISITE_UNQUALIFIED')
            check(not focus_path.exists() and denied['snapshot']==prerequisite['snapshot']
                  and denied['snapshot_error']==prerequisite['snapshot_error']
                  and denied['original_review']==answer and denied['result']['reason']==expected_reason
                  and prerequisite['snapshot_error']==error
                  and prerequisite['semantic_consistent'] is semantic
                  and prerequisite['original_review']==answer
                  and prerequisite['minimum_sequence']==prerequisite_min
                  and original_app_snapshot==prerequisite['snapshot']
                  and prerequisite['boundary_ns']>receipt_clock
                  and focus_first_checked is not None
                  and prerequisite['boundary_ns']>focus_first_checked
                  and denial_required
                  and guard_records[0]['result']['reason']=='FOCUS_NOT_TARGET'
                  and paired['focus_recovery']==denied
                  and denied['result']['status']=='YIELD'
                  and denied['result']['task_complete'] is False
                  and denied['result']['native_calls']==[] and len(guard_records)==1
                  and paired['guard_final']==denied['result'], 'GUARD_FOCUS_DENIED_OUTCOME_JOIN')
        if denied_path.exists():
            check(paired['guard_final']==read(denied_path)['result'],'GUARD_FINAL_RESULT_JOIN')
        elif focus_path.exists() and not native_completed(read(focus_path)['report']):
            check(paired['guard_final']['reason']=='FOCUS_RECOVERY_NATIVE_INCOMPLETE'
                  and paired['guard_final']['status']=='YIELD'
                  and paired['guard_final']['task_complete'] is False
                  and paired['guard_final']['native_calls']==[],'GUARD_FINAL_RESULT_JOIN')
        else:
            check(paired['guard_final']==guard_records[-1]['result'],'GUARD_FINAL_RESULT_JOIN')
        for arm in ('control','guard'):
            check(Counter(canonical(value['result']) for value in all_reports[arm])==
                  Counter(canonical(value) for value in raw_by_arm[arm]),'NATIVE_UNREPORTED_OR_REPLAYED_INPUT')
            programs = list((pair/arm/'native').glob('guarded-session-*/program-guarded-*.json'))
            check(len(programs)==sum(value['result'].get('input_dispatched') is not False for value in all_reports[arm]),
                  'NATIVE_PROGRAM_UNREPORTED_INPUT')
        calls = [first]+([recovery] if recovery else [])
        for call in calls:
            check(call['parsed']['call_id'] not in call_ids,'PROCESS_CALL_ID_REUSED')
            call_ids.add(call['parsed']['call_id'])
            usage.update(call['parsed']['usage'])
            cli_calls+=1
        check(paired['cli_calls']==len(calls),'PROCESS_PAIR_CALL_COUNT')
        rows.append(dict(id=schedule['id'],cli_calls=len(calls)))
    check(used_slots==slots and {path.name for path in (root/'exchange').iterdir()}==slots,
          'PROCESS_SLOT_ACCOUNTING')
    check(outcome['rows']==rows and cli_calls<=2*len(rows),'PROCESS_STUDY_CALL_COUNT')
    formal = plan.get('formal_allocation') is True
    if formal:
        check(not gaps,'FORMAL_METHOD_GATES_INCOMPLETE:'+','.join(sorted(set(gaps))))
        check(plan.get('model',{}).get('name') and plan['model'].get('effort'),'FORMAL_REQUESTED_MODEL_MISSING')
        for name in ('paired_audit.py','file_audit.py'):
            path = Path(__file__).resolve().parent/name
            key = '/src/research/integration/tk_model_task_guard_5260_a15_wslc_20261004/'+name
            check(plan['source_sha256'].get(key)==digest(path.read_bytes()),'FORMAL_AUDITOR_SOURCE_NOT_FROZEN')
        for frozen in host['plans'].values():
            argv = frozen['argv']
            check('--model' in argv and argv[argv.index('--model')+1]==plan['model']['name']
                  and 'model_reasoning_effort="'+plan['model']['effort']+'"' in argv,
                  'FORMAL_REQUESTED_MODEL_ARGV_JOIN')
    return dict(schema='a15-saved-paired-audit-v1',formal_allocation=formal,
        method_disposition='METHOD_INCOMPLETE' if gaps else 'METHOD_PASS_FINITE_LOCAL',
        gaps=sorted(set(gaps)),cli_calls=cli_calls,usage=dict(usage),
        quality={arm:dict(values) for arm,values in quality.items()},
        rows=rows,provider_performance_claim=False,requested_model_attested=False,
        scope='FINITE_COOPERATIVE_SAVED_CUSTODY_NOT_AUTHENTICATED_ATTESTATION')


if __name__=='__main__':
    print(json.dumps(audit(sys.argv[1]),sort_keys=True))
