"""Raw-only primary batch audit. Does not execute archived sources or infer pixels."""
import base64,hashlib,json,tarfile
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()

def load(root):
    manifest=json.loads((root/'raw-manifest.json').read_text())
    if sha((root/'raw.tar.gz').read_bytes())!=manifest['archive_sha256']:raise ValueError('archive digest')
    with tarfile.open(root/'raw.tar.gz') as archive:
        members=archive.getmembers()
        if any(not m.isfile() for m in members) or len({m.name for m in members})!=len(members):raise ValueError('archive inventory')
        package={m.name:archive.extractfile(m).read() for m in members}
    if set(package)!=set(manifest['files']):raise ValueError('manifest inventory')
    for name,data in package.items():
        if len(data)!=manifest['files'][name]['bytes'] or sha(data)!=manifest['files'][name]['sha256']:raise ValueError('manifest member')
    return package

def check(package):
    def require(condition,reason):
        if not condition:raise ValueError(reason)
    def read(name):return json.loads(package[name])
    plan=read('case/PLAN.json')
    for name,expected in plan['hashes'].items():require(sha(package['case/'+name])==expected,'frozen source '+name)
    require(read('case/session/allocation.json')['source']==plan['source'],'allocation source')
    history=[json.loads(line) for line in package['case/session/submission-history.jsonl'].splitlines()]
    require(len(history)==1 and history[0]['path']=='/save' and history[0]['body']=='value=completion1001064','exact once value')
    require(read('case/session/finish.json')['primary_state']['stopped'] is None,'primary stopped')
    require(read('host/exit.json')['code']==0,'host exit')
    cleanup=read('case/session/cleanup.json');require(all(c['returncode'] is not None for c in cleanup),'live child')
    request_names=sorted((int(k.split('request-')[1].split('.')[0]),k) for k in package if k.startswith('host/request-'))
    require([n for n,_ in request_names]==list(range(1,9)),'request census')
    requests={n:read(name) for n,name in request_names}
    require([r['tool'] for r in requests.values()]==['interface_guarded_observe','interface_guarded_mint_many','interface_guarded_input','interface_guarded_input','interface_guarded_mint','interface_guarded_input','interface_guarded_observe','interface_close'],'no replay schedule')
    events=[json.loads(line) for line in package['host/host-events.jsonl'].splitlines()]
    metas={}
    for attempt,request in requests.items():
        reply=read(f'host/reply-{attempt}.json')
        require(reply['tool']==request['tool'] and reply['result'].get('isError') is not True,'reply mismatch/error')
        content=reply['result']['content'];meta=json.loads(next(c['text'] for c in content if c['type']=='text'));metas[attempt]=meta
        if attempt in (1,3,4,6,7):
            image=base64.b64decode(next(c['data'] for c in content if c['type']=='image'),validate=True)
            require(sha(image)==meta['source']['native']['artifact']['sha256'],'image digest')
            artifact_name=Path(meta['source']['native']['artifact']['path']).name
            native=[v for k,v in package.items() if k=='case/session/server/'+meta['call_id']+'/images/'+artifact_name]
            require(len(native)==1 and native[0]==image,'native image')
            review=read(f'host/review-{attempt}.json')
            require(review['reply_sha256']==sha(package[f'host/reply-{attempt}.json']) and review['images'][0]['sha256']==sha(image),'review binding')
            kinds={e['kind']:e['sequence'] for e in events if e.get('attempt')==attempt}
            next_send=next(e['sequence'] for e in events if e.get('attempt')==attempt+1 and e['kind']=='send_requested')
            require(kinds['presentation_callbacks_completed']<kinds['review_recorded']<next_send,'review order')
        else:
            ack=read(f'host/text-acknowledgment-{attempt}.json')
            require(ack['reply_sha256']==sha(package[f'host/reply-{attempt}.json']),'text ack binding')
    batch=metas[2];refs=requests[2]['arguments']['references']
    require(requests[2]['arguments']['source_sequence']==metas[1]['source']['sequence']==batch['source_sequence'],'batch source')
    require(batch['status']=='minted' and batch['input_dispatched'] is False and len(batch['minted'])==len(refs)==2,'complete no-input batch')
    require([r['alias'] for r in refs]==['batch_field','batch_save_hover'],'declared aliases')
    for declared,minted in zip(refs,batch['minted']):
        require(declared['alias']==minted['alias'] and minted['offset']==[v//2 for v in declared['region_size']],'ordered batch inventory')
        lifetime=minted['lifetime'];require(lifetime['clock']=='time.monotonic_ns' and lifetime['expires_ns']>lifetime['minted_ns'] and lifetime['authority_granted'] is False,'finite no-authority lifetime')
    require(requests[5]['arguments']['source_sequence']==metas[4]['source']['sequence'],'reviewed hover source')
    require(requests[5]['arguments']['alias']==metas[5]['alias']=='batch_save_click' and metas[5]['status']=='minted','explicit unique click reference')
    emissions=0;wait_ms=0
    for attempt,alias,interaction in ((3,'batch_field','click'),(4,'batch_save_hover','move'),(6,'batch_save_click','click')):
        args=requests[attempt]['arguments'];meta=metas[attempt]
        require(args['alias']==alias and args['interaction']==interaction,'guarded input choice')
        require(meta['status']=='completed','input completion')
        execution=meta['result']['execution'];releases=execution['releases']
        require(bool(releases) and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'neutral input')
        guards=meta['result'].get('guard_checks',meta['result'].get('guard_summary',{}).get('checks',[]))
        require(bool(guards) and all(g['status']=='VALID' and g['handle']==alias for g in guards),'fresh guards')
        emissions+=execution['program_emissions'];wait_ms+=sum(w['requested_ms'] for w in execution['waits'])
    require(metas[7]['input_dispatched'] is False and metas[7]['source']['sequence']>metas[6]['source']['sequence'],'fresh no-input observation')
    require(len({m['session']['session_id'] for m in metas.values()})==1,'session continuity')
    close=metas[8]['release'];require(close['verified'] is True and close['keys_down']==[] and close['buttons_down']==[],'neutral close')
    return dict(status='PASS_PRIMARY_BATCH_MECHANICS_SCOPED',exact_submissions=1,calls=8,programs=3,program_emissions=emissions,requested_wait_ms=wait_ms,original_images=5,initial_batch_references=2,initial_batch_calls=1,explicit_hover_remints=1,extra_observations=1,cleanup=cleanup,visual_scope='Primary-declared cue; raw audit does not infer semantic pixels')

if __name__=='__main__':print(json.dumps(check(load(Path(__file__).parent)),indent=2))
