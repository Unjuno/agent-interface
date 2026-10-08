import hashlib,io,json,pathlib,subprocess,tarfile,tempfile
folder=pathlib.Path(__file__).parent
records=[]
def run(name,command,expected):
    p=subprocess.run(command,text=True,capture_output=True)
    records.append({'name':name,'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'expected_success':expected})
    if (p.returncode==0)!=expected: raise ValueError(name)
run('normal',['python3',str(folder/'verify.py')],True)
run('optimized',['python3','-O',str(folder/'verify.py')],True)
with tarfile.open(folder/'raw.tar.gz') as tf: original={m.name:tf.extractfile(m).read() for m in tf.getmembers()}
for mode in ['archive-corruption','missing-member','wrong-score','refusal-input-emitted']:
    with tempfile.TemporaryDirectory() as d:
        dest=pathlib.Path(d);raw=dict(original)
        if mode=='missing-member': raw.pop('presented-readonly/host/review-2.json')
        if mode=='wrong-score':
            name='presented-readonly/session/evaluation-at-close.json';v=json.loads(raw[name]);v['record_count']=1;raw[name]=json.dumps(v).encode()
        if mode=='refusal-input-emitted':
            name='presented-readonly/host/reply-2.json';v=json.loads(raw[name]);block=next(b for b in v['result']['content'] if b['type']=='text');meta=json.loads(block['text']);meta['result']['input_dispatched']=True;block['text']=json.dumps(meta);raw[name]=json.dumps(v).encode();digest=hashlib.sha256(raw[name]).hexdigest()
            ename='presented-readonly/host/host-events.jsonl';events=[json.loads(l) for l in raw[ename].splitlines()]
            for e in events:
                if e.get('attempt')==2 and 'reply_sha256' in e: e['reply_sha256']=digest
            raw[ename]=(''.join(json.dumps(e)+'\n' for e in events)).encode()
            rname='presented-readonly/host/review-2.json';rv=json.loads(raw[rname]);rv['reply_sha256']=digest;raw[rname]=json.dumps(rv).encode()
        with tarfile.open(dest/'raw.tar.gz','w:gz') as tf:
            for name,data in raw.items():
                member=tarfile.TarInfo(name);member.size=len(data);tf.addfile(member,io.BytesIO(data))
        manifest={'archive_sha256':hashlib.sha256((dest/'raw.tar.gz').read_bytes()).hexdigest(),'members':{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}}
        if mode=='missing-member': manifest['members']=json.loads((folder/'manifest.json').read_text())['members']
        (dest/'manifest.json').write_text(json.dumps(manifest))
        if mode=='archive-corruption':
            data=bytearray((dest/'raw.tar.gz').read_bytes());data[-1]^=1;(dest/'raw.tar.gz').write_bytes(data)
        run(mode,['python3',str(folder/'verify.py'),str(dest)],False)
with (folder/'verification-results.json').open('x') as f: json.dump(records,f,indent=2)
print(json.dumps({'verified':len(records),'countercontrols':4}))
