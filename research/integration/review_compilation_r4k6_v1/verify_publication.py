"""Read-only transport reconstruction; no new review matrix or native action."""
import base64
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
LIMIT = 4_000_000


def decode(root, item):
    text = ''.join((root / name).read_text().strip() for name in item['parts'])
    if len(text) > LIMIT:
        raise ValueError('transport too large')
    packed = base64.b64decode(text, validate=True)
    if len(packed) != item['packed_bytes'] or hashlib.sha256(packed).hexdigest() != item['packed_sha256']:
        raise ValueError('transport identity mismatch')
    decoder = lzma.LZMADecompressor(memlimit=256_000_000)
    raw = decoder.decompress(packed, max_length=LIMIT + 1)
    if len(raw) > LIMIT or not decoder.eof or decoder.unused_data:
        raise ValueError('invalid compressed framing')
    if len(raw) != item['raw_bytes'] or hashlib.sha256(raw).hexdigest() != item['raw_sha256']:
        raise ValueError('raw identity mismatch')
    return raw


def main():
    manifest = json.loads((HERE / 'RECORD_TRANSPORT.json').read_text())
    data = {name: decode(HERE, item) for name, item in manifest.items()}
    with tempfile.TemporaryDirectory(prefix='review-records-') as td:
        root = Path(td)
        for name in ('audit.py', 'controls.py', 'io_data.py', 'verify_saved.py',
                     'FREEZE.json', 'INPUTS.json', 'RECORDS.json', 'AUDIT.json', 'CONTROLS.json'):
            shutil.copy2(HERE / name, root / name)
        shutil.copytree(HERE / 'input_parts', root / 'input_parts')
        (root / 'records.b64').write_text(base64.b64encode(zlib.compress(data['evaluation'], 9)).decode() + '\n')
        completed = subprocess.run([sys.executable, '-S', '-B', str(root / 'verify_saved.py')],
                                   capture_output=True, text=True, timeout=20)
        if completed.returncode:
            raise ValueError('frozen audit failed: ' + completed.stderr)
        # A distinct prefreeze input-loader version produced construction.
        # Its exact raw data and source maps are preserved, not substituted into the evaluation.
        construction = json.loads(data['construction'])
        if construction['count'] != 18 or len(construction['rows']) != 18:
            raise ValueError('construction denominator mismatch')
        print(json.dumps({'status': 'PASS_EXACT_RAW_TRANSPORT', 'evaluation_rows': 180,
                          'construction_rows': 18, 'new_matrix_runs': 0,
                          'frozen_verifier': json.loads(completed.stdout)}, sort_keys=True))


if __name__ == '__main__':
    main()
