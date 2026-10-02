"""Read-only audit; image semantics remain an explicit primary declaration."""
import base64, hashlib, json, tarfile
from pathlib import Path


def load(root):
    if (root/'raw.tar.gz').exists():
        manifest=json.loads((root/'raw-manifest.json').read_text())
        if hashlib.sha256((root/'raw.tar.gz').read_bytes()).hexdigest()!=manifest['archive_sha256']:
            raise ValueError('archive digest mismatch')
        with tarfile.open(root/'raw.tar.gz') as archive:
            members=archive.getmembers()
            if any(not m.isfile() for m in members) or len({m.name for m in members})!=len(members):
                raise ValueError('non-file or repeated archive member')
            package={m.name:archive.extractfile(m).read() for m in members}
        if set(package)!=set(manifest['files']):raise ValueError('manifest inventory mismatch')
        for name,data in package.items():
            if len(data)!=manifest['files'][name]['bytes'] or hashlib.sha256(data).hexdigest()!=manifest['files'][name]['sha256']:
                raise ValueError('manifest member mismatch')
        return package
    return {p.relative_to(root).as_posix():p.read_bytes() for directory in ('case','host')
            for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def check(package):
    def require(condition, reason):
        if not condition:raise ValueError(reason)
    def read(name):return json.loads(package[name])
    def sha(data):return hashlib.sha256(data).hexdigest()
    plan=read('case/PLAN.json')
    for name, expected in plan['hashes'].items():
        require(sha(package['case/'+name])==expected,'frozen source changed '+name)
    require(read('case/session/allocation.json')['source']==plan['source'],'allocation source')
    records=[json.loads(line) for line in package['case/session/submission-history.jsonl'].splitlines()]
    require(len(records)==1 and records[0]['path']=='/save' and records[0]['body']=='value=completion1001063','exact once submission')
    require(read('case/session/finish.json')['primary_state']['stopped'] is None,'primary stopped')
    require(read('host/exit.json')['code']==0,'host exit')
    require(all(row['returncode'] is not None for row in read('case/session/cleanup.json')),'live child')
    requests=sorted((int(k.split('request-')[1].split('.')[0]),read(k)) for k in package if k.startswith('host/request-'))
    require([n for n,_ in requests]==list(range(1,8)),'request inventory')
    require([r['tool'] for _,r in requests]==['interface_observe','interface_clock','interface_dispatch','interface_clock','interface_dispatch','interface_observe','interface_close'],'no replay schedule')
    metas={};images={}
    events=[json.loads(line) for line in package['host/host-events.jsonl'].splitlines()]
    for attempt,request in requests:
        reply=read(f'host/reply-{attempt}.json')
        require(reply['tool']==request['tool'] and reply['result'].get('isError') is not True,'reply mismatch or error')
        content=reply['result']['content'];meta=json.loads(next(c['text'] for c in content if c['type']=='text'));metas[attempt]=meta
        if attempt in (1,3,5,6):
            image=base64.b64decode(next(c['data'] for c in content if c['type']=='image'),validate=True)
            ref=meta['image_reference'];images[attempt]=ref
            require(sha(image)==ref['sha256'],'image digest')
            native=[data for name,data in package.items() if name.startswith('case/session/server/'+meta['call_id']+'/images/') and name.endswith('.png')]
            require(len(native)==1 and native[0]==image,'original native PNG equality')
            review=read(f'host/review-{attempt}.json')
            require(review['reply_sha256']==sha(package[f'host/reply-{attempt}.json']) and review['images'][0]['sha256']==sha(image),'review binding')
            kinds={e['kind']:e['sequence'] for e in events if e.get('attempt')==attempt}
            require(kinds['presentation_callbacks_completed']<kinds['review_recorded'],'presentation/review order')
            if attempt<7:
                next_send=next(e['sequence'] for e in events if e.get('attempt')==attempt+1 and e['kind']=='send_requested')
                require(kinds['review_recorded']<next_send,'review before next request')
        else:
            require(f'host/text-acknowledgment-{attempt}.json' in package,'missing text acknowledgement')
        if attempt in (3,5):
            require(meta['outcome_summary']['execution_status']=='completed','incomplete input')
            releases=meta['receipt']['execution_summary']['releases']
            require(bool(releases) and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'non-neutral program')
    fresh=metas[6]['receipt']['source']['raw_report']
    require(fresh['input_dispatched'] is False and fresh['side_effect_authority'] is False,'observation input')
    require(metas[5]['session']['session_id']==metas[6]['session']['session_id'],'connection changed')
    require(images[5]['post_dispatch_observation_id']!=images[6]['observation_id'],'historical capture reused')
    require(images[6]['capture_ns']>images[5]['recorded_capture']['capture_ended_ns'],'fresh acquisition order')
    close=metas[7]['release']
    require(close['verified'] is True and close['keys_down']==[] and close['buttons_down']==[],'close release')
    emissions=sum(metas[a]['receipt']['execution_summary']['program_emissions'] for a in (3,5))
    return dict(status='PASS_COMPLETION_OBSERVATION_MECHANICS_SCOPED',exact_submissions=1,calls=7,programs=2,program_emissions=emissions,original_images=4,extra_observations=1,
                visual_scope='primary-declared cue from original PNG; audit does not infer image semantics',
                cleanup=read('case/session/cleanup.json'))


if __name__=='__main__':
    print(json.dumps(check(load(Path(__file__).parent)),indent=2))
