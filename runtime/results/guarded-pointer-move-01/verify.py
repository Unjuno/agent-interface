"""Hash-check and safely extract all retained trials, then recompute semantics."""
import hashlib, json, pathlib, sys, tarfile, tempfile
from analyze import analyze, require

def verify(folder):
    folder = pathlib.Path(folder)
    manifest = json.loads((folder/'manifest.json').read_text())
    archive = folder/'raw.tar.gz'
    require(hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256'], 'archive hash')
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        with tarfile.open(archive, 'r:gz') as tf:
            members = tf.getmembers()
            require(len(members)==len(manifest['members']) and {m.name for m in members}==set(manifest['members']), 'member inventory')
            for member in members:
                path = pathlib.PurePosixPath(member.name)
                require(member.isfile() and not path.is_absolute() and '..' not in path.parts, 'unsafe member')
                data = tf.extractfile(member).read()
                require(hashlib.sha256(data).hexdigest()==manifest['members'][member.name], 'member hash '+member.name)
                destination = root/member.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
        result = analyze(root)
        require(result==json.loads((folder/'analysis.json').read_text()), 'recomputed analysis')
        return {'status':result['status'], 'members':len(members), 'scope':result['scope']}

if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).parent), indent=2))
