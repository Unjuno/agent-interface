import base64,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SCHEMA='agent-interface/guarded-feedback-observation-refs-v1'
MAP={'/observation_report/observation':'/source/native','/feedback/observation':'/source'}
def require(value,message):
    if not value:raise ValueError(message)
def reconstruct(meta):
    full=copy.deepcopy(meta)
    if 'reference_schema' not in full:return full
    require(full['reference_schema']==SCHEMA and full['observation_references']==MAP,'reference mapping')
    require(full['feedback']['observation']=={'observation_ref':'/source'},'feedback reference redirect')
    require(full['observation_report']['observation']=={'observation_ref':'/source/native'},'native reference redirect')
    full['feedback']['observation']=copy.deepcopy(full['source'])
    full['observation_report']['observation']=copy.deepcopy(full['source']['native'])
    for key in ['reference_schema','observation_references','reference_scope']:full.pop(key)
    return full

def validate(meta,full_report,events,expected):
    full=reconstruct(meta)
    require(all(full[key]==value for key,value in full_report.items()),'original report changed')
    require(full['result']['status']=='completed','input incomplete')
    releases=full['result']['execution']['releases']
    require(bool(releases) and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'non-neutral release')
    cue=full['feedback'];require(cue['status']==expected,'cue verdict')
    require(full['task_success'] is None and full['replay_allowed'] is False,'success/replay inference')
    require(cue['task_success'] is None and cue['authority_granted'] is False and cue['input_dispatched'] is False,'cue authority')
    require(cue['observation']==full['source'],'source association')
    require(sum(e['event']=='save' and e['token']=='t1001069' for e in events)==1,'independent Save count')
    if expected=='matched':
        require(cue['title']==cue['after_title']=='SAVED-1001069','matched title')
        acks=[e for e in events if e['event']=='app_ack']
        require(len(acks)==1 and acks[0]['status']=='SAVED','independent Saved ack')
        require(cue['started_ns']<acks[0]['ns']<=cue['samples'][-1]['known_ns'],'ack chronology')
        require(meta['reference_schema']==SCHEMA,'missing compression')
    else:
        require(cue['title']==cue['after_title']=='PENDING-1001069' and full['status']=='needs_review','pending status')
        require('reference_schema' not in meta,'critical evidence projected')
    return full

def audit():
    rows=[]
    manifest=json.loads((ROOT/'frozen-manifest.json').read_text());archive=ROOT/'frozen-runtime.pyz'
    require(hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['sha256'],'archive hash')
    host_manifest=ROOT/'frozen-host/HOST_MANIFEST.json';host_info=json.loads(host_manifest.read_text())
    require(host_info['source_revision']==manifest['source_revision'],'source split')
    for record in host_info['files']:
        require(hashlib.sha256((host_manifest.parent/record['path']).read_bytes()).hexdigest()==record['sha256'],'host bytes')
    for name,expected in [('01-matched','matched'),('02-pending','pending')]:
        case=ROOT/name;cleanup=json.loads((case/'cleanup.json').read_text());terminal=json.loads((case/'host-terminal.json').read_text())
        require(cleanup['host_exit']==0 and cleanup['child_exit_codes']==[0,-15,0],'owner cleanup')
        require(terminal['exit']=={'code':0,'signal':None},'relay transport cleanup')
        allocation=json.loads((case/'allocation.json').read_text())
        require(allocation['archive_sha256']==manifest['sha256'] and allocation['host_manifest_sha256']==hashlib.sha256(host_manifest.read_bytes()).hexdigest(),'allocation changed')
        replies=[json.loads(p.read_text()) for p in sorted((case/'host').glob('reply-*.json'))]
        tools=[r['tool'] for r in replies];wanted=['interface_guarded_observe','interface_guarded_mint','interface_guarded_input']
        if expected=='matched':wanted.append('interface_results')
        wanted.append('interface_close');require(tools==wanted,'unexpected call/replay')
        row=replies[2];text=row['result']['content'][0]['text'];meta=json.loads(text)
        full_report=json.loads((case/'calls'/meta['call_id']/'report.json').read_text())
        events=[json.loads(line) for line in (case/'events.jsonl').read_text().splitlines()]
        full=validate(meta,full_report,events,expected)
        bridge=next((case/'calls').glob('guarded-session-*'))
        native_inputs=list(bridge.glob('result-*.json'));native_cues=list(bridge.glob('feedback-*.json'))
        require(len(native_inputs)==len(native_cues)==1,'extra native execution')
        require(json.loads(native_inputs[0].read_text())==full['result'],'native input receipt changed')
        require(json.loads(native_cues[0].read_text())==full['feedback'],'native cue changed')
        require(len(list(bridge.glob('observation-*.json')))==6,'extra native captures')
        for attempt,index in [(1,1),(3,4)]:
            reply=replies[attempt-1];picture=reply['result']['content'][1]
            png=(case/f'primary-{index:03d}.png').read_bytes()
            require(png==base64.b64decode(picture['data']),'primary PNG bytes')
            rm=json.loads(reply['result']['content'][0]['text'])
            require(hashlib.sha256(png).hexdigest()==rm['source']['native']['artifact']['sha256'],'PNG provenance')
            review=json.loads((case/'host'/f'review-{attempt}.json').read_text())
            require(review['reply_sha256']==hashlib.sha256((case/'host'/f'reply-{attempt}.json').read_bytes()).hexdigest(),'review association')
        if expected=='matched':
            fetched=json.loads(replies[3]['result']['content'][0]['text'])
            require(all(fetched[k]==v for k,v in full_report.items()),'retrieved full evidence changed')
            require(fetched['operation_invoked'] is False,'retrieval replayed input')
            require(terminal['caller_state']['stopped'] is None,'unexpected caller STOP')
        else:require(bool(terminal['caller_state']['stopped']),'missing caller STOP')
        sent=[json.loads(s) for s in (case/'host/host-events.jsonl').read_text().splitlines()]
        require([e['tool'] for e in sent if e['kind']=='send_requested']==wanted,'host request census')
        control=json.loads((case/'replies/004.json').read_text())
        original_bytes=len(json.dumps(full,allow_nan=False).encode())
        rows.append({'case':name,'cue':expected,'control_requests':len(replies),'primary_images':2,
          'native_captures':6,'input_programs':1,'save_count':1,'task_completed':expected=='matched',
          'returned_text_bytes':len(text.encode()),'same_metadata_expanded_bytes':original_bytes,
          'byte_difference':original_bytes-len(text.encode()),
          'input_call_ms':(int(control['ended_ns'])-int(control['started_ns']))/1e6,
          'primary_semantic_awareness_ms':None,'tokens_for_reply':None,'billing_for_reply':None})
    return rows
if __name__=='__main__':print(json.dumps(audit(),indent=2))
