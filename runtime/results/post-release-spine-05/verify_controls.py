"""Rehashed corruption must still fail semantic verification."""
import hashlib,importlib.util,json,pathlib,tarfile,tempfile
root=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('verify05',root/'verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
results=[]
for control in ['wrong-score','held-key','hidden-direct-input']:
    with tempfile.TemporaryDirectory() as tmp:
        base=pathlib.Path(tmp);raw=base/'raw';raw.mkdir();out=base/'out';out.mkdir()
        with tarfile.open(root/'raw.tar.gz') as tf:tf.extractall(raw,filter='data')
        if control=='wrong-score':
            p=raw/'guarded-local/session/evaluation-at-close.json';data=json.loads(p.read_text());data['exact_counts']['task-6']=1
        elif control=='held-key':
            p=raw/'guarded-local/host/reply-41.json';data=json.loads(p.read_text());meta=json.loads(data['result']['content'][0]['text']);meta['release']['keys_down']=['CTRL'];data['result']['content'][0]['text']=json.dumps(meta)
        else:
            p=raw/'direct-post/host/request-4.json';data=json.loads(p.read_text());data['tool']='interface_dispatch'
        p.write_text(json.dumps(data))
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
