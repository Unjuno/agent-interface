"""Rehash mutations so semantic rejection is tested beyond archive integrity."""
import hashlib,json,pathlib,tarfile,tempfile
from verify import verify

def controls():
    original=pathlib.Path(__file__).parent
    outcomes={}
    for name in ['wrong_score','refusal_dispatched_input','wrong_review_image']:
        with tempfile.TemporaryDirectory() as tmp:
            folder=pathlib.Path(tmp);raw=folder/'raw';raw.mkdir()
            with tarfile.open(original/'raw.tar.gz','r:gz') as tf:
                for member in tf.getmembers():
                    path=raw/member.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(tf.extractfile(member).read())
            if name=='wrong_score':
                path=raw/'guarded-local/session/evaluation-at-close.json';value=json.loads(path.read_text());value['exact_counts']['task-6']=1
            elif name=='refusal_dispatched_input':
                path=raw/'guarded-local/host/reply-42.json';value=json.loads(path.read_text());meta=json.loads(value['result']['content'][0]['text']);meta['result']['input_dispatched']=True;value['result']['content'][0]['text']=json.dumps(meta)
            else:
                path=raw/'direct-post/host/review-8.json';value=json.loads(path.read_text());value['images'][0]['sha256']='0'*64
            path.write_text(json.dumps(value,indent=2)+'\n')
            if name=='refusal_dispatched_input':
                review=raw/'guarded-local/host/review-42.json';value=json.loads(review.read_text());value['reply_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();review.write_text(json.dumps(value,indent=2)+'\n')
            files=sorted(x for x in raw.rglob('*') if x.is_file())
            with tarfile.open(folder/'raw.tar.gz','w:gz') as tf:
                for path in files:tf.add(path,arcname=path.relative_to(raw).as_posix(),recursive=False)
            manifest={'archive_sha256':hashlib.sha256((folder/'raw.tar.gz').read_bytes()).hexdigest(),'members':{p.relative_to(raw).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
            (folder/'manifest.json').write_text(json.dumps(manifest))
            try:verify(folder)
            except ValueError as error:outcomes[name]={'rejected':True,'reason':str(error)}
            else:raise RuntimeError('accepted mutation '+name)
    return outcomes

if __name__=='__main__':print(json.dumps(controls(),indent=2))
