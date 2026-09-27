"""Restore verified flat result files only. No network or live experiment execution."""
import base64
import hashlib
import json
import zlib
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    root = Path(__file__).resolve().parent
    m = json.loads((root/'RESULTS_MANIFEST.json').read_text())
    packed = base64.b64decode((root/'results.zlib.b64').read_text().strip(), validate=True)
    require(len(packed) == m['compressed_bytes'], 'compressed length')
    require(hashlib.sha256(packed).hexdigest() == m['compressed_sha256'], 'compressed hash')
    decoder = zlib.decompressobj()
    raw = decoder.decompress(packed, 1000000)
    require(decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data, 'compression boundary')
    require(len(raw) == m['uncompressed_bytes'], 'decoded length')
    require(hashlib.sha256(raw).hexdigest() == m['uncompressed_sha256'], 'decoded hash')
    files = json.loads(raw)
    require(set(files) == set(m['files']), 'file set')
    for name, text in files.items():
        require(Path(name).name == name and name not in ('', '.', '..'), 'flat path')
        require(isinstance(text, str), 'file encoding')
        data = text.encode('utf-8')
        require(hashlib.sha256(data).hexdigest() == m['files'][name], 'file hash: '+name)
        target = root/name
        require(not target.is_symlink(), 'symlink target')
        if target.exists():
            require(target.read_bytes() == data, 'refuse overwrite: '+name)
    for name, text in files.items():
        if not (root/name).exists():
            with (root/name).open('xb') as out:
                out.write(text.encode('utf-8'))
    print('PASS_LOSSLESS_RESTORE: '+str(len(files))+' files; no live experiment executed')


if __name__ == '__main__':
    main()
