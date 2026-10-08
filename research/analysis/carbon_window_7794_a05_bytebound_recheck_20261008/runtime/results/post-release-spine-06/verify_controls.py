"""Rehashed corruption must still fail semantic verification."""
import hashlib,importlib.util,json,pathlib,tarfile,tempfile
root=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('verify06',root/'verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
results=[]
for control in ['wrong-score','held-key','hidden-control-input']:
    with tempfile.TemporaryDirectory() as tmp:
        base=pathlib.Path(tmp);raw=base/'raw';raw.mkdir();out=base/'out';out.mkdir()
        with tarfile.open(root/'raw.tar.gz') as tf:tf.extractall(raw,filter='data')
        if control=='wrong-score':
            p=raw/'guarded-local/session/evaluation-at-close.json';data=json.loads(p.read_text());data['exact_counts']['task-6']=1
        elif control=='held-key':
            p=raw/'direct-post/host/reply-29.json';data=json.loads(p.read_text());meta=json.loads(data['result']['content'][0]['text']);meta['release']['keys_down']=['CTRL'];data['result']['content'][0]['text']=json.dumps(meta)
        else:
            p=raw/'guarded-local/host/reply-40.json';data=json.loads(p.read_text());meta=json.loads(data['result']['content'][0]['text']);meta['input_dispatched']=True;data['result']['content'][0]['text']=json.dumps(meta)
        p.write_text(json.dumps(data))
        if control!='wrong-score':
            attempt=29 if control=='held-key' else 40
            route='direct-post' if control=='held-key' else 'guarded-local'
            event_path=raw/route/'host/host-events.jsonl'
            events=[json.loads(line) for line in event_path.read_text().splitlines()]
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            for event in events:
                if event.get('attempt')==attempt and 'reply_sha256' in event:event['reply_sha256']=digest
            event_path.write_text(''.join(json.dumps(event)+'\n' for event in events))
        members={}
        with tarfile.open(out/'raw.tar.gz','w:gz') as tf:
            for p in sorted(raw.rglob('*')):
                if not p.is_file():continue
                name=p.relative_to(raw).as_posix();members[name]=hashlib.sha256(p.read_bytes()).hexdigest();tf.add(p,arcname=name)
        (out/'manifest.json').write_text(json.dumps({'archive_sha256':hashlib.sha256((out/'raw.tar.gz').read_bytes()).hexdigest(),'members':members}))
        try:v.verify(out)
        except (ValueError,KeyError) as e:results.append({'control':control,'rejected':True,'reason':str(e)})
        else:raise RuntimeError('accepted '+control)
print(json.dumps(results,indent=2))
