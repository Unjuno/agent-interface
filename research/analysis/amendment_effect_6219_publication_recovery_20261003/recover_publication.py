"""Recover a publication bit-shift; preserve every original Git blob unchanged."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

SOURCE = 'c9743221a9478b0a7d2bb3cbf9cd4cde87ca9cb3'
PREFIX = 'research/analysis/amendment_effect_6219_t0_20261002/'
PACKAGE = Path(__file__).resolve().parent
EXPECTED_OUTPUTS = {
    'results/allocation-01/candidate/candidate_raw.json': '23012f286e31b6e96d1b7ad5167d0ef36dba2bb050c80efc2bff8e38986ba376',
    'results/allocation-01/audit/audit.json': '8fde90b8353467faacd89e5407611d6bceafcdd9c1da26aa0c2ccaf4485c3023',
}


def inverse_prefix(blob):
    encoded = base64.b64encode(blob)
    if not encoded.startswith(b't'):
        raise ValueError('unexpected publication prefix')
    return base64.b64decode(encoded[1:] + b'=')


def hash_bound_restore(blob, expected):
    prefix = inverse_prefix(blob)
    candidates = [(prefix, None)] + [(prefix + bytes([value]), value) for value in range(256)]
    matches = [(data, suffix) for data, suffix in candidates if hashlib.sha256(data).hexdigest() == expected]
    if len(matches) != 1:
        raise ValueError('no unique hash-bound restoration')
    return matches[0]


def generate():
    # Mechanical recovery only; never executes candidate/auditor or changes the source ref.
    if any((PACKAGE / name).exists() for name in ('published_blobs', 'decoded_material', 'unbound_derivatives', 'RECOVERY_MANIFEST.json')):
        raise SystemExit('STOP_RECOVERY_OUTPUT_COLLISION')
    entries = subprocess.check_output(['git', 'ls-tree', '-r', SOURCE, PREFIX]).decode().splitlines()
    originals = {}
    for entry in entries:
        metadata, path = entry.split('\t', 1)
        original = subprocess.check_output(['git', 'cat-file', 'blob', metadata.split()[2]])
        originals[path[len(PREFIX):]] = (metadata.split()[2], original)
    if len(originals) != 14:
        raise SystemExit('STOP_SOURCE_CARDINALITY')
    frozen = json.loads(inverse_prefix(originals['FREEZE.json'][1]))
    expected = dict(frozen['sha256'])
    expected.update(EXPECTED_OUTPUTS)
    if len(expected) != 11:
        raise SystemExit('STOP_REFERENCE_CARDINALITY')
    witness = json.loads(subprocess.check_output(['gh', 'api', 'repos/Unjuno/agent-interface/pulls/6644']))
    if witness['head']['sha'] != SOURCE or any(digest not in witness['body'] for digest in EXPECTED_OUTPUTS.values()):
        raise SystemExit('STOP_PR_REFERENCE_MISMATCH')
    records = []
    outputs = []
    for relative, (git_blob, published) in originals.items():
        archived = 'published_blobs/' + relative + '.bin'
        outputs.append((archived, published))
        if relative in expected:
            recovered, suffix = hash_bound_restore(published, expected[relative])
            destination = 'decoded_material/' + relative
            status = 'EXACT_SHA256_REFERENCE_MATCH'
        else:
            recovered, suffix = inverse_prefix(published), None
            destination = 'unbound_derivatives/' + relative + '.decoded-prefix.txt'
            status = 'UNBOUND_DECODED_PREFIX_NOT_PROVEN_ORIGINAL_BYTES'
        recovered.decode('utf-8')
        outputs.append((destination, recovered))
        records.append({'source_path': PREFIX + relative, 'source_git_blob': git_blob,
                        'published_sha256': hashlib.sha256(published).hexdigest(),
                        'archived_path': archived, 'derivative_path': destination,
                        'derivative_sha256': hashlib.sha256(recovered).hexdigest(),
                        'expected_sha256': expected.get(relative), 'appended_byte': suffix,
                        'status': status})
    manifest = {'source_tip': SOURCE, 'source_pr': 6644, 'original_blobs': 14,
                'hash_bound_files': 11, 'unbound_prefix_derivatives': 3,
                'recipe': 'base64_encode(blob); remove leading ASCII t; base64_decode with one added padding =; accept base or exactly one appended byte only on unique pre-existing SHA256 match',
                'formal_reruns': 0, 'scientific_disposition': 'METHOD_FAIL', 'files': records}
    outputs.append(('PR6644_RECORDED_DISPOSITION.txt', (witness['body'] + '\n').encode()))
    outputs.append(('RECOVERY_MANIFEST.json', (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()))
    for relative, payload in outputs:
        destination = PACKAGE / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    print(json.dumps({'original_blobs': 14, 'hash_bound_files': 11, 'unbound_prefix_derivatives': 3, 'formal_reruns': 0}))


if __name__ == '__main__':
    if sys.argv[1:] != ['--generate']:
        raise SystemExit('use --generate once at a fresh recovery path')
    generate()
