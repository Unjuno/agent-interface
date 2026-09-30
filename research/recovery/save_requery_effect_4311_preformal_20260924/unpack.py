"""Verify and restore evidence without executing it; destination must be new."""
import base64, hashlib, io, json, lzma, pathlib, sys, tarfile

def restore(manifest_path, destination):
    mp = pathlib.Path(manifest_path).resolve()
    dest = pathlib.Path(destination).resolve()
    m = json.loads(mp.read_text())
    if dest.exists():
        raise ValueError('destination already exists')
    pieces = []
    for part in m['parts']:
        rel = pathlib.PurePosixPath(part['path'])
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('invalid part path')
        data = (mp.parent / rel).read_bytes()
        if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
            raise ValueError('part integrity: ' + str(rel))
        pieces.append(data.strip())
    compressed = base64.b64decode(b''.join(pieces), validate=True)
    if len(compressed) != m['decoded_bytes'] or hashlib.sha256(compressed).hexdigest() != m['decoded_sha256']:
        raise ValueError('archive integrity')
    decoder = lzma.LZMADecompressor()
    expanded = decoder.decompress(compressed, max_length=134217729)
    if not decoder.eof or decoder.unused_data or len(expanded) != m['expanded_bytes'] or len(expanded) > 134217728:
        raise ValueError('expansion limit or length')
    verified = {}
    with tarfile.open(fileobj=io.BytesIO(expanded), mode='r:') as tf:
        for member in tf:
            rel = pathlib.PurePosixPath(member.name)
            if not member.isfile() or rel.is_absolute() or '..' in rel.parts or str(rel) in verified:
                raise ValueError('unsafe member')
            if str(rel) not in m['files']:
                raise ValueError('unexpected member')
            data = tf.extractfile(member).read()
            if hashlib.sha256(data).hexdigest() != m['files'][str(rel)]:
                raise ValueError('member hash')
            verified[str(rel)] = data
    if set(verified) != set(m['files']):
        raise ValueError('missing member')
    dest.mkdir(parents=True)
    for name, data in verified.items():
        p = dest / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    print(json.dumps({'files':len(verified), 'archive_sha256':m['decoded_sha256'], 'executed':False}))

if __name__ == '__main__':
    restore(sys.argv[1], sys.argv[2])
