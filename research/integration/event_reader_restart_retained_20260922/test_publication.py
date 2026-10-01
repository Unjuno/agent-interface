"""Read-only publication checks; no producer, GUI, model or formal runner."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import unpack


def main():
    source = Path(__file__).resolve().parent
    results = []
    with tempfile.TemporaryDirectory(prefix='publication3989-') as temporary:
        root = Path(temporary)
        restored = root / 'restored'
        result = unpack.restore(source, restored)
        original = unpack.load(source)
        got = {str(p.relative_to(restored)): p.read_bytes()
               for p in restored.rglob('*') if p.is_file()}
        assert original == got
        results.append({'check': 'restore_exact_members', 'passed': True, **result})
        negatives = [
            ('missing_part', lambda p: (p / 'evidence.01.b64').unlink()),
            ('changed_part', lambda p: (p / 'evidence.02.b64').write_text('changed\n')),
            ('oversized_part', lambda p: (p / 'evidence.03.b64').write_bytes(b'A' * 9002)),
            ('changed_manifest_identity', lambda p: mutate_manifest(p, 'json_sha256', '0' * 64)),
            ('reordered_parts', reorder_parts),
        ]
        for name, mutate in negatives:
            damaged = root / name
            shutil.copytree(source, damaged)
            mutate(damaged)
            destination = root / (name + '-out')
            try:
                unpack.restore(damaged, destination)
            except (OSError, ValueError):
                assert not destination.exists()
                results.append({'check': name, 'rejected': True, 'no_output': True})
            else:
                raise AssertionError(name)
        before = got
        try:
            unpack.restore(source, restored)
        except FileExistsError:
            after = {str(p.relative_to(restored)): p.read_bytes()
                     for p in restored.rglob('*') if p.is_file()}
            assert before == after
            results.append({'check': 'existing_destination', 'rejected': True, 'unchanged': True})
        else:
            raise AssertionError('existing_destination')
        text_map = {name: value.decode() for name, value in original.items()}
        bad = copy.deepcopy(text_map)
        value = bad.pop(next(iter(bad)))
        bad[unpack.ROOTS[0] + '../escape'] = value
        try:
            unpack.validate_members(bad)
        except ValueError as error:
            assert str(error) == 'MEMBER_PATH'
            results.append({'check': 'parent_path', 'rejected': True})
        else:
            raise AssertionError('parent_path')
        try:
            json.loads('{"x": 1, "x": 2}', object_pairs_hook=unpack.unique)
        except ValueError:
            results.append({'check': 'duplicate_json_key', 'rejected': True})
        else:
            raise AssertionError('duplicate_json_key')
        v2 = restored / unpack.ROOTS[1]
        evidence = v2 / 'evidence/formal-01'
        for script, expected in [
            ('audit_bounded.py', '90bfc03cbb797789227cf742e2c96af02b5dc103ca64f94759a3fd6a1531a906'),
            ('test_bounded_audit.py', 'ae1e6c1dc9cf98e552902d62b6a4b6f1a3228a87083883a6586986122524f438'),
        ]:
            command = [sys.executable, str(v2 / script), str(evidence)]
            p = subprocess.run(command, capture_output=True, timeout=15,
                               env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            digest = hashlib.sha256(p.stdout).hexdigest()
            assert p.returncode == 0 and p.stderr == b'' and digest == expected
            results.append({'check': script, 'exit': p.returncode, 'stdout_sha256': digest,
                            'stderr_bytes': len(p.stderr), 'original_output_identical': True})
    print(json.dumps({'status': 'PASS_PUBLICATION_REVALIDATION', 'checks': results,
                      'formal_invocations': 0}, indent=2, sort_keys=True))


def mutate_manifest(path, key, value):
    target = path / 'MANIFEST.json'
    manifest = json.loads(target.read_text())
    manifest[key] = value
    target.write_text(json.dumps(manifest))


def reorder_parts(path):
    target = path / 'MANIFEST.json'
    manifest = json.loads(target.read_text())
    manifest['parts'].reverse()
    target.write_text(json.dumps(manifest))


if __name__ == '__main__':
    main()
