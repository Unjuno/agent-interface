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
    check(any(result==raw for raw in raw_results),'NATIVE_ORIGINAL_RESULT_JOIN')
    execution = result.get('execution',{})
    check(positive(execution.get('started_ns')) and execution['started_ns']<=execution['ended_ns'],
          'NATIVE_EXECUTION_CLOCK')
    releases = execution.get('releases',[])
    check(bool(releases) and all(value.get('verified') is True and value.get('keys_down')==[]
          and value.get('buttons_down')==[] and execution['started_ns']<=value['monotonic_ns']<=execution['ended_ns']
          for value in releases),'NATIVE_RELEASE_NOT_EMPTY')
    return execution


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
    if not outcome.get('local_sources'):
        gaps.append('SOURCE_LOCAL_FINAL_CLOSURE_MISSING')
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
            all_reports['control'].append(call['report'])
        check(not control['native_calls'] if answer['decision']=='REFUSE' else
              [call['tail'] for call in control['native_calls']]==
              ([list([dict(op='key_chord',keys=['Home']),dict(op='text',text=answer['prefix'])])]
               if answer['decision']=='INSERT_PREFIX' else [])+[[dict(op='key_chord',keys=['CTRL','s'])]],
              'CONTROL_MODEL_INTENT_CHANGED')
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
                reason = qualification(current,app_data['guard'][2],current['nonce'],review['minimum_sequence'],
                    review['response_seen_ns'],review['checked_ns'],review['maximum_age_ns'])
            reason = reason or semantic_reason(record['review'],current,schedule['wanted'])
            check(record['plan']['reason']==reason,'GUARD_DECISION_RECONSTRUCTION')
            if record['plan']['status']=='YIELD':
                check(record['result']['native_calls']==[],'GUARD_YIELD_EMITTED_TASK_INPUT')
            for call in record['result']['native_calls']:
                execution = native_report(call['report'],raw_by_arm['guard'])
                all_reports['guard'].append(call['report'])
                check(current['completed_ns']<=execution['started_ns']<=execution['ended_ns']<=call['finished_ns'],
                      'NATIVE_ADMISSION_CLOCK_JOIN')
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
                        error = qualification(snapshot,app_data['guard'][2],snapshot['nonce'],constraint['minimum_sequence'],
                            constraint['boundary_ns'],constraint['checked_ns'],constraint['maximum_age_ns'])
                        check(constraint['error']==error and original['eligible']==(error is None),
                              'NATIVE_CURRENT_CHECK_RECONSTRUCTION')
                    if constraint['error'] is None:
                        expected_text = record['plan'].get('prior_target') if call['purpose']=='prefix' else schedule['wanted']
                        check(snapshot['target']==expected_text and snapshot['decoy']=='','NATIVE_TASK_DEPENDENCY_CHANGED')
                if call['purpose']=='prefix':
                    check(call['tail']==[dict(op='key_chord',keys=['Home']),dict(op='text',text=record['review']['prefix'])],
                          'NATIVE_MODEL_PREFIX_REPLACED')
                    effects = [value['reply']['snapshot'] for value in native_snapshots if value['purpose']=='repair-effect']
                    check(len(effects)==1 and effects[0]['started_ns']>call['finished_ns']
                          and effects[0]['target']==schedule['wanted'] and effects[0]['decoy']=='','NATIVE_REPAIR_EFFECT_JOIN')
                    validations = [read(path) for path in (pair/'guard/native').glob('effect-validation-*.json')]
                    if not validations:
                        gaps.append(schedule['id']+':DECISION_CLOCK_EFFECT_MISSING')
                    else:
                        check(len(validations)==1 and validations[0]['snapshot']==effects[0]
                              and validations[0]['proposal']==record['plan']
                              and validations[0]['action_finished_ns']==call['finished_ns'],'NATIVE_EFFECT_VALIDATION_JOIN')
                        value = validations[0]
                        check(qualification(effects[0],app_data['guard'][2],value['request_nonce'],value['minimum_sequence'],
                            value['action_finished_ns'],value['checked_ns'],value['maximum_age_ns']) is None
                            and value['save_plan']['status']=='PLAN_SAVE','NATIVE_EFFECT_VALIDATION_CHANGED')
                elif call['purpose']=='save':
                    check(call['tail']==[dict(op='key_chord',keys=['CTRL','s'])],'NATIVE_SAVE_INTENT_CHANGED')
                else:
                    raise ValueError('NATIVE_UNEXPECTED_TASK_OPERATION')
        focus_path = pair/'focus-recovery.json'
        if focus_path.exists():
            focus = read(focus_path)
            check(paired['focus_recovery']==focus and guard_records[0]['result']['reason']=='FOCUS_NOT_TARGET'
                  and recovery is None and schedule['focus_drift'] is True,'GUARD_FOCUS_CONTEXT')
            execution = native_report(focus['report'],raw_by_arm['guard'])
            all_reports['guard'].append(focus['report'])
            check(receipt_clock==focus['original_response_seen_ns'] and execution['ended_ns']<=focus['click_finished_ns']
                  and len(guard_records)==2 and guard_records[1]['review']==answer
                  and guard_records[1]['response_seen_ns']==max(receipt_clock,focus['click_finished_ns']),
                  'GUARD_FOCUS_NEW_ACK_BOUNDARY')
            prerequisite = pair/'focus-prerequisite.json'
            if not prerequisite.exists():
                gaps.append(schedule['id']+':DECISION_CLOCK_FOCUS_MISSING')
            else:
                value = read(prerequisite)
                check(value['original_review']==answer and value['semantic_consistent'] is True
                      and lookup.get(value['request_nonce'])==value['snapshot']
                      and value['checked_ns']<=execution['started_ns'], 'GUARD_FOCUS_PREREQUISITE_JOIN')
                error = qualification(value['snapshot'],app_data['guard'][2],value['request_nonce'],value['minimum_sequence'],
                    value['boundary_ns'],value['checked_ns'],value['maximum_age_ns'])
                check(error in (None,'FOCUS_NOT_TARGET') and value['snapshot_error']==error
                      and semantic_reason(answer,value['snapshot'],schedule['wanted']) in
                      ('CURRENT_TASK_EXACT','CURRENT_PREFIX_REPAIR'),'GUARD_FOCUS_NOT_SEMANTIC_ONLY')
        check(paired['guard_final']==guard_records[-1]['result'],'GUARD_FINAL_RESULT_JOIN')
        for arm in ('control','guard'):
            check(len(all_reports[arm])==len(raw_by_arm[arm]) and
                  {value['result']['execution']['started_ns'] for value in all_reports[arm]}==
                  {value['execution']['started_ns'] for value in raw_by_arm[arm]},'NATIVE_UNREPORTED_OR_REPLAYED_INPUT')
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
