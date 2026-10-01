import hashlib,json,pathlib,tarfile,tempfile
from verify import verify

def controls():
    original=pathlib.Path(__file__).parent;results={}
    for name in ['renewed_lookup','wrong_duration','held_key_at_close']:
        with tempfile.TemporaryDirectory() as tmp:
            folder=pathlib.Path(tmp);raw=folder/'raw';raw.mkdir()
            with tarfile.open(original/'raw.tar.gz','r:gz') as tf:
                for m in tf.getmembers():
                    p=raw/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(m).read())
            attempts=[6] if name=='renewed_lookup' else [4,6] if name=='wrong_duration' else [7]
            for attempt in attempts:
                p=raw/f'guarded-local/host/reply-{attempt}.json';r=json.loads(p.read_text());meta=json.loads(r['result']['content'][0]['text'])
                if name=='held_key_at_close':meta['release']['keys_down']=['SHIFT']
                else:meta['minted'][0]['lifetime']['expires_ns']+=1
                r['result']['content'][0]['text']=json.dumps(meta);p.write_text(json.dumps(r,indent=2)+'\n')
            files=sorted(x for x in raw.rglob('*') if x.is_file())
            with tarfile.open(folder/'raw.tar.gz','w:gz') as tf:
                for p in files:tf.add(p,arcname=p.relative_to(raw).as_posix(),recursive=False)
            (folder/'manifest.json').write_text(json.dumps({'archive_sha256':hashlib.sha256((folder/'raw.tar.gz').read_bytes()).hexdigest(),'members':{p.relative_to(raw).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}))
            try:verify(folder)
            except ValueError as e:results[name]={'rejected':True,'reason':str(e)}
            else:raise RuntimeError('mutation accepted '+name)
    return results

if __name__=='__main__':print(json.dumps(controls(),indent=2))
