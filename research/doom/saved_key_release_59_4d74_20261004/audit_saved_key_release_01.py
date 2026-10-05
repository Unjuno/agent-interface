from pathlib import Path
import json,hashlib,collections
root=Path('/study');out=Path('/out')
path=root/'controller-recovery-01/episode/runtime/events.jsonl'
owner_path=root/'controller-recovery-01/episode/runtime/owner-events.json'
events=[json.loads(x) for x in path.read_text().splitlines()]
owners=json.loads(owner_path.read_text())
accepted={x['id']:x for x in events if x.get('event')=='accepted'}
admissions=[x for x in events if x.get('event')=='input_admission']
releases=[x for x in events if x.get('event')=='input_release_transition']
joins=[]
for release in releases:
    fields=('id','step','key','owner_id','intent_token','valid_until_ns')
    matched=[x for x in admissions if all(x.get(k)==release.get(k) for k in fields)]
    assert len(matched)==1
    admission=matched[0];program=accepted[release['id']]
    assert program['intent_token']==release['intent_token']
    receipt=release['owner_thread_keyup_receipt']
    assert receipt in owners
    assert all(receipt[k]==release[k] for k in ('key','owner_id','intent_token','valid_until_ns'))
    lo=release['release_call_started_ns'];hi=release['release_call_returned_ns']
    start=receipt['owner_keyrelease_started_ns'];end=receipt['owner_sync_returned_ns']
    assert admission['admitted_ns']<=admission['input_ack_ns']<=lo<=start<=end<=hi
    assert receipt['server_sync_completed'] is True
    assert receipt['physical_verification_authoritative'] is False
    joins.append({'id':release['id'],'step':release['step'],'key':release['key'],
                  'owner_keyrelease_started_ns':start,'owner_sync_returned_ns':end,
                  'release_call_started_ns':lo,'release_call_returned_ns':hi,
                  'native_release_bracket_ns':end-start,
                  'physical_or_application_release_identified':False})
result={'disposition':'PASS_IDENTITY_BOUND_SERVER_SYNC_BRACKETS_SCOPED',
        'admission_count':len(admissions),'release_count':len(releases),'joins':joins,
        'per_key_exact_physical_release':'UNIDENTIFIED',
        'useful_task_feedback':'NOT_TESTED_BY_THIS_AUDIT',
        'raw_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (path,owner_path)}}
(out/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
