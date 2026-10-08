"""Verify retained real-X11 composition evidence; never infer six-task success."""
import base64, hashlib, json, pathlib, sys, tarfile

def require(ok, message):
    if not ok:
        raise ValueError(message)

def verify(folder):
    folder = pathlib.Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text())
    archive = folder / 'raw.tar.gz'
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['archive_sha256'], 'archive hash')
    with tarfile.open(archive, 'r:gz') as tf:
        members = tf.getmembers()
        require(all(m.isfile() and not pathlib.PurePosixPath(m.name).is_absolute() and '..' not in pathlib.PurePosixPath(m.name).parts for m in members), 'unsafe member')
        require(len(members) == len(manifest['members']) and {m.name for m in members} == set(manifest['members']), 'member inventory')
        raw = {m.name: tf.extractfile(m).read() for m in members}
    for name, digest in manifest['members'].items():
        require(hashlib.sha256(raw[name]).hexdigest() == digest, 'member hash: ' + name)
    read = lambda name: json.loads(raw[name])
    plan = read('LIVE_PLAN.json')
    for name, digest in plan['hashes'].items():
        require(hashlib.sha256(raw[name]).hexdigest() == digest, 'pinned source: ' + name)
    allocation = read('presented-readonly/session/allocation.json')
    require(allocation['seed'] == 1001043 and allocation['display'] == ':153' and allocation['source'].startswith('0155942a0'), 'allocation')
    prefix = 'presented-readonly/host/'
    events = [json.loads(line) for line in raw[prefix+'host-events.jsonl'].splitlines()]
    require([e['sequence'] for e in events] == list(range(1, 21)), 'event sequence')
    require([e['host_monotonic_ms'] for e in events] == sorted(e['host_monotonic_ms'] for e in events), 'event order')
    tools = ['interface_guarded_observe','interface_guarded_input','interface_guarded_review_window','interface_close']
    metas = []
    for attempt, tool in enumerate(tools, 1):
        req = read(prefix+f'request-{attempt}.json')
        reply_name = prefix+f'reply-{attempt}.json'
        reply = read(reply_name)
        require(req['tool'] == reply['tool'] == tool and req['id'] == reply['id'] == attempt and reply['status'] == 'returned', 'request/reply identity')
        es = [e for e in events if e.get('attempt') == attempt]
        kinds = ['send_requested','reply_available','presentation_started','presentation_callbacks_completed'] + (['review_recorded'] if attempt < 4 else [])
        require([e['kind'] for e in es] == kinds, 'send/presentation/review order')
        digest = hashlib.sha256(raw[reply_name]).hexdigest()
        require(all(e.get('reply_sha256', digest) == digest for e in es), 'retained reply identity')
        content = reply['result']['content']
        meta = json.loads(next(c['text'] for c in content if c['type'] == 'text'))
        metas.append(meta)
        images = [c for c in content if c['type'] == 'image']
        require(len(images) == (1 if attempt < 4 else 0), 'image delivery inventory')
        if attempt < 4:
            review = read(prefix+f'review-{attempt}.json')
            png = base64.b64decode(images[0]['data'], validate=True)
            png_digest = hashlib.sha256(png).hexdigest()
            require(review['reply_sha256'] == digest and review['images'][0]['sha256'] == png_digest and review['source_sequence'] == meta['source']['sequence'], 'review identity')
            artifact = meta['source']['native']['artifact']
            matches = [b for n,b in raw.items() if n.endswith('/images/'+pathlib.PurePosixPath(artifact['path']).name)]
            require(len(matches) == 1 and matches[0] == png and artifact['sha256'] == png_digest, 'actual native PNG')
    refused = metas[1]
    require(read(prefix+'reply-2.json')['result']['isError'] is True and refused['status'] == 'refused' and refused['result']['input_dispatched'] is False, 'typed refusal without input')
    require(refused['result']['guard_checks'][0]['reason'] == 'unknown_session_alias', 'refusal reason')
    require(metas[2]['review']['previous_binding_revision'] == 0 and metas[2]['review']['binding_revision'] == 1 and metas[2]['input_dispatched'] is False, 'explicit read-only repair')
    release = metas[3]['release']
    require(metas[3]['status'] == 'closed' and release['verified'] is True and release['keys_down'] == release['buttons_down'] == [], 'neutral close')
    require(read(prefix+'exit.json') == {'code':0,'signal':None} and events[-1]['kind'] == 'transport_closed' and events[-1]['code'] == 0, 'relay exit')
    require(read('original-handle-terminal.json')['exit_code'] == 0, 'original fixture exit')
    score = read('presented-readonly/session/evaluation-at-close.json')
    require(score['success'] is False and score['record_count'] == 0 and len(score['missing']) == 6 and not score['unexpected'] and not score['duplicates'], 'read-only scorer outcome')
    require(read('green.json')['exit_code'] == 0 and 'pass 29' in read('green.json')['output'], 'related tests')
    return {'scope':'read-only real-X11 API composition; not task or autonomous recovery pass','public_calls':4,'images_presented_and_reviewed':3,'refusal_input_dispatched':False,'binding_revision':[0,1],'independent_submissions':0,'relay_exit':0,'fixture_exit':0,'cleanup_returncodes':[r['returncode'] for r in read('presented-readonly/session/cleanup.json')],'members':len(raw)}

if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).parent), indent=2))
