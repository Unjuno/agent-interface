"""Semantic countercontrols with intact archive hashes; never invokes input."""
import copy, hashlib, json, pathlib, tarfile, tempfile
from verify import verify

def controls():
    original = pathlib.Path(__file__).parent
    rejected = []
    for control in ('wrong_score','hidden_press'):
        with tempfile.TemporaryDirectory() as td:
            folder = pathlib.Path(td)
            (folder/'analysis.json').write_bytes((original/'analysis.json').read_bytes())
            with tarfile.open(original/'raw.tar.gz','r:gz') as tf:
                data = {m.name:tf.extractfile(m).read() for m in tf.getmembers()}
            if control == 'wrong_score':
                name = 'trial-03/guarded-local/session/evaluation-at-close.json'
                row = json.loads(data[name]); row['exact_counts']['task-3']=1
            else:
                candidates = [(name,json.loads(value)) for name,value in data.items()
                              if '/guarded-session-' in name and '/program-' in name]
                name,row = next((name,row) for name,row in candidates
                                if [x['op'] for x in row['ops']]==['focus','pointer_move','wait_update','release_all'])
                row['ops'].insert(2,{'op':'pointer_button','button':'left','down':True})
            data[name] = (json.dumps(row)+'\n').encode()
            archive = folder/'raw.tar.gz'
            with tarfile.open(archive,'w:gz') as tf:
                import io
                for name,value in data.items():
                    member = tarfile.TarInfo(name); member.size=len(value)
                    tf.addfile(member,io.BytesIO(value))
            (folder/'manifest.json').write_text(json.dumps({
                'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                'members':{name:hashlib.sha256(value).hexdigest() for name,value in data.items()}}))
            try: verify(folder)
            except ValueError as error: rejected.append({'control':control,'reason':str(error)})
            else: raise ValueError('countercontrol accepted: '+control)
    return rejected

if __name__ == '__main__': print(json.dumps(controls(),indent=2))
