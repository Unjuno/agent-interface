"""Bounded data-only restoration; destination parent must be trusted."""
from pathlib import Path, PurePosixPath
import base64, hashlib, io, json, lzma, sys, tarfile
LIMIT = 64 * 1024 * 1024

def need(ok, why):
    if not ok:
        raise ValueError(why)

def relative(name):
    p = PurePosixPath(name)
    need(isinstance(name, str) and name and not p.is_absolute()
         and '..' not in p.parts and '\\' not in name and str(p) == name,
         'unsafe path')
    return p

def digest(data):
    return hashlib.sha256(data).hexdigest()

def restore(manifest_path, destination):
    manifest_path, destination = Path(manifest_path), Path(destination)
    need(not destination.exists(), 'destination already exists')
    m = json.loads(manifest_path.read_text())
    need(m['format'] == 'tar.xz/base64' and 0 < m['archive_bytes'] <= LIMIT
         and 0 < m['tar_bytes'] <= LIMIT and 0 < len(m['parts']) <= 256
         and 0 < len(m['members']) <= 20000, 'archive bounds')
    encoded = []
    for item in m['parts']:
        p = manifest_path.parent / relative(item['path'])
        need(p.is_file() and not p.is_symlink() and p.stat().st_size <= LIMIT,
             'invalid part')
        b = p.read_bytes()
        need(len(b) == item['bytes'] and digest(b) == item['sha256'], 'part hash')
        encoded.append(b.strip())
    need(sum(map(len, encoded)) <= 2 * LIMIT, 'encoded bounds')
    compressed = base64.b64decode(b''.join(encoded), validate=True)
    need(len(compressed) == m['archive_bytes']
         and digest(compressed) == m['archive_sha256'], 'archive hash')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    data = decoder.decompress(compressed, max_length=LIMIT + 1)
    need(len(data) == m['tar_bytes'] and len(data) <= LIMIT
         and decoder.eof and not decoder.unused_data, 'decompression bounds')
    pending, seen, total = [], set(), 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
        for entry in archive:
            name = str(relative(entry.name))
            need(entry.isfile() and name not in seen and name in m['members'],
                 'member type/name')
            seen.add(name)
            info = m['members'][name]
            total += entry.size
            need(0 <= entry.size <= LIMIT and total <= LIMIT
                 and entry.size == info['bytes'], 'member bounds')
            b = archive.extractfile(entry).read()
            need(digest(b) == info['sha256'], 'member hash')
            pending.append((name, b))
    need(seen == set(m['members']), 'member inventory')
    destination.mkdir(parents=False, exist_ok=False)
    for name, b in pending:
        p = destination / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(b)
    return len(pending)

if __name__ == '__main__':
    need(len(sys.argv) == 3, 'usage: unpack.py MANIFEST NEW_DESTINATION')
    print(restore(sys.argv[1], sys.argv[2]))
