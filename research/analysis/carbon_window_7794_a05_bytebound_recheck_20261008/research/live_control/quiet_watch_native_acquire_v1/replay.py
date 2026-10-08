#!/usr/bin/env python3
"""Offline, hash-checked replay and negative controls. Python stdlib only."""
import argparse, base64, copy, hashlib, json, tempfile
from pathlib import Path
from audit import audit
from codec import unpack

HERE = Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def replay(destination):
    if not __debug__:
        raise RuntimeError('assertions required; do not use python -O')
    manifest = json.loads((HERE/'manifest.json').read_text())
    assert sha((HERE/'codec.py').read_bytes()) == manifest['codec_sha256']
    blocks = []
    for entry in manifest['parts']:
        p = (HERE/entry['path']).resolve()
        assert HERE in p.parents
        b = p.read_bytes()
        assert len(b) == entry['bytes'] and sha(b) == entry['sha256']
        assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest() == entry['git_blob']
        blocks.append(b)
    packed = b''.join(blocks)
    assert len(packed) == manifest['archive_bytes']
    assert sha(packed) == manifest['archive_sha256']
    raw = unpack(packed)
    assert len(raw) == manifest['raw_bytes'] and sha(raw) == manifest['raw_sha256']
    destination.mkdir(parents=True, exist_ok=False)
    path = destination/'raw.json'
    path.write_bytes(raw)
    result = audit(path, HERE/'prereg.json')
    summary = {k:v for k,v in result.items() if k != 'case_stats'}
    assert summary == json.loads((HERE/'result.json').read_text())
    (destination/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return raw, summary

def negative_controls(raw):
    original = json.loads(raw)
    variants = {}
    for name in ('pixel_tamper','count_tamper','release_tamper','schedule_swap',
                 'source_tamper','negative_cpu','deadline_tamper','key_down_tamper'):
        obj = copy.deepcopy(original)
        r = obj['records'][0]
        if name == 'pixel_tamper':
            key = next(iter(r['pixel_payloads']))
            b = bytearray(base64.b64decode(r['pixel_payloads'][key])); b[0] ^= 1
            r['pixel_payloads'][key] = base64.b64encode(b).decode()
        elif name == 'count_tamper': r['acquisitions'][0]['match_count'] += 1
        elif name == 'release_tamper': r['owner']['verified_empty'] = False
        elif name == 'schedule_swap': obj['records'][0],obj['records'][1] = obj['records'][1],obj['records'][0]
        elif name == 'source_tamper': obj['sources']['native.c'] = '0'*64
        elif name == 'negative_cpu': r['acquisition_metrics'][0][2] = -1
        elif name == 'deadline_tamper': r['owner']['deadline_ns'] += 1
        elif name == 'key_down_tamper': r['right_down_final'] = True
        variants[name] = obj
    results = {}
    with tempfile.TemporaryDirectory(prefix='qnative-negative-') as d:
        for name,obj in variants.items():
            path = Path(d)/(name+'.json'); path.write_text(json.dumps(obj))
            try:
                audit(path, HERE/'prereg.json')
            except AssertionError:
                results[name] = 'REJECTED'
            else:
                raise RuntimeError('mutated evidence accepted: '+name)
    assert results == json.loads((HERE/'negative_controls.json').read_text())
    return results

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True)
    args = ap.parse_args()
    raw,summary = replay(args.out.resolve())
    negatives = negative_controls(raw)
    print(json.dumps(dict(decision=summary['decision'],cases=summary['cases'],
        frames_reclassified=summary['frames_reclassified'],raw_sha256=sha(raw),
        negative_controls=negatives),indent=2,sort_keys=True))
