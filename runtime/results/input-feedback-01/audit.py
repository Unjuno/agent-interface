import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def require(condition,message):
    if not condition:raise ValueError(message)

def validate(row,events,expected):
    meta=row['metadata'];cue=meta['feedback'];result=meta['result']
    require(result['status']=='completed','input receipt lost')
    releases=result['execution']['releases']
    require(bool(releases) and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'non-neutral release')
    require(meta['task_success'] is None and meta['replay_allowed'] is False,'false success/replay claim')
    require(cue['status']==expected,'cue verdict')
    require(cue['task_success'] is None and cue['authority_granted'] is False and cue['input_dispatched'] is False,'cue authority')
    require(meta['status']==('completed' if expected=='matched' else 'needs_review'),'top status')
    require(row['isError'] is (expected!='matched'),'error indication')
    require(meta['source']==cue['observation'],'capture association')
    require(row['image_sha256']==meta['source']['native']['artifact']['sha256'],'delivered image association')
    require(cue['title']==cue['after_title']==cue['samples'][-1]['title'],'unstable cue')
    title={'matched':'SAVED','rejected':'REJECTED','pending':'PENDING'}[expected]+'-1001068'
    require(cue['title']==title,'title verdict mismatch')
    require(any(s['title']=='PENDING-1001068' for s in cue['samples']),'missing live pending transition')
    require(cue['started_ns']>=result['execution']['ended_ns'],'feedback before release')
    require(all(a['known_ns']<=b['known_ns'] for a,b in zip(cue['samples'],cue['samples'][1:])),'sample order')
    require(sum(e['event']=='save' for e in events)==1,'save replay')
    if expected!='pending':
        acks=[e for e in events if e['event']=='app_ack']
        require(len(acks)==1 and acks[0]['status']==title.split('-')[0],'independent app ack')
        require(cue['started_ns']<acks[0]['ns']<=cue['samples'][-1]['known_ns'],'delayed ack timing')
    # Pending is an observation at the deadline, not a claim about eventual app
    # outcome: application work can continue after this reply.
    return {'cue':expected,'call_ms':(row['ended_ns']-row['started_ns'])/1e6,
        'local_cue_wait_ms':(cue['ended_ns']-cue['started_ns'])/1e6,
        'local_cue_known_from_call_ms':(cue['samples'][-1]['known_ns']-row['started_ns'])/1e6,
        'sample_count':len(cue['samples']),'save_count':1,
        'primary_semantic_awareness_ms':None,'model_tokens':None,'billing':None}

def audit():
    rows=[]
    archive=ROOT/'frozen-runtime.pyz';digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    for name,expected in [('01-matched','matched'),('02-rejected','rejected'),('03-pending','pending')]:
        case=ROOT/name;cleanup=json.loads((case/'cleanup.json').read_text())
        require(cleanup['closed'] is True and all(type(c) is int for c in cleanup['child_exit_codes']),'owner not terminal')
        require(json.loads((case/'allocation.json').read_text())['archive_sha256']==digest,'archive changed')
        replies=[json.loads(p.read_text()) for p in sorted((case/'replies').glob('*.json'))]
        require([r['request']['tool'] for r in replies]==['interface_guarded_observe','interface_guarded_mint','interface_guarded_input','interface_close'],'unexpected request/retry')
        require(len(list((case/'commands').glob('*.json')))==4,'extra queued command')
        for reply in replies:
            if reply['image_path']:
                image=case/Path(reply['image_path']).name
                require(hashlib.sha256(image.read_bytes()).hexdigest()==reply['image_sha256'],'image bytes')
        events=[json.loads(s) for s in (case/'events.jsonl').read_text().splitlines()]
        row=validate(replies[2],events,expected);row.update(case=name,control_requests=4,primary_images=2)
        rows.append(row)
    return rows

if __name__=='__main__':print(json.dumps(audit(),indent=2))
