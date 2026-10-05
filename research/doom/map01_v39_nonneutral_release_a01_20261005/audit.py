import hashlib, json, pathlib
root = pathlib.Path(__file__).resolve().parent
lock = json.loads((root / 'SOURCE_LOCK.json').read_text(encoding='utf-8'))
manifest = {}
for line in (root / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest, name = line.split('  ', 1)
    manifest[name] = digest
actual_names = {p.name for p in root.iterdir() if p.is_file() and p.name != 'SHA256SUMS'}
assert set(manifest) == actual_names, 'manifest file set mismatch'
for name, expected in manifest.items():
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    assert actual == expected, f'manifest sha256 mismatch: {name}'
for name, expected in lock['sha256'].items():
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    assert actual == expected, f'source lock sha256 mismatch: {name}'
def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + bytes([0]) + data).hexdigest()
assert git_blob_sha(root / 'baseline_input_owner_v13.py') == lock['parent_owner_blob']
assert git_blob_sha(root / 'published_input_owner_v13.py') == lock['published_candidate_owner_blob']
old = "            if down or buttons_down:" + chr(10) + "                raise RuntimeError('owner release not verified: ' + repr(down))"
new = "            if down or buttons_down:" + chr(10) + "                release_error = RuntimeError('owner release not verified: ' + repr(down))" + chr(10) + "                fault = release_error" + chr(10) + "                active = None" + chr(10) + "                raise release_error"
base = (root / 'published_input_owner_v13.py').read_text(encoding='utf-8')
fixed = (root / 'input_owner_v14_candidate.py').read_text(encoding='utf-8')
assert base.count(old) == 1 and base.replace(old, new) == fixed, 'candidate delta is not the stated minimal patch'
test = (root / 'test_non_neutral_release.py').read_text(encoding='utf-8')
assert 'test_non_neutral_successful_aggregate_must_fail_closed' in test
assert "rec['keys_down'],[75]" in test
assert 'self.assertNotIn(98,D.physical)' in test
parent = (root / 'PARENT-RED.log').read_text(encoding='utf-8-sig')
published = (root / 'PUBLISHED-CANDIDATE-RED.log').read_text(encoding='utf-8-sig')
green = (root / 'CANDIDATE-GREEN.log').read_text(encoding='utf-8-sig')
assert 'Ran 1 test' in parent and 'FAILED (failures=1)' in parent and 'RuntimeError not raised' in parent
assert 'Ran 3 tests' in published and 'FAILED (failures=1)' in published
assert published.count(' ... ok') == 2 and 'RuntimeError not raised' in published
assert 'Ran 3 tests' in green and 'OK' in green and 'FAILED' not in green
print('PASS: complete file manifest; source SHA-256/Git blob locks; one-hunk patch; parent focused RED; published candidate RED with two controls; patched candidate GREEN 3/3')