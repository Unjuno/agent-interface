"""Retained process/file observations only; never run owner, peer or collector."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/reviews/accepted_child_input_6919_7772_20261003'
PACKET = ROOT / REL
SOURCE = 'bb9be23e4b8f5eac15812b32f9dd941925cf97de'


def load(name):
    return json.loads((PACKET / name).read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def module(name):
    spec = importlib.util.spec_from_file_location('retained_' + name, PACKET / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def retained_check():
    freeze, repair = load('FREEZE.json'), load('REAUDIT_FREEZE.json')
    for name, digest in freeze['files'].items():
        require(sha((PACKET / name).read_bytes()) == digest, 'frozen source ' + name)
    for name, key in [('audit_v2.py', 'auditor_sha256'), ('matrix-v1/raw.jsonl', 'raw_sha256'),
                      ('FREEZE.json', 'original_freeze_sha256'), ('audit.py', 'original_auditor_sha256'),
                      ('REAUDIT.md', 'description_sha256')]:
        require(sha((PACKET / name).read_bytes()) == repair[key], 're-audit pin ' + name)
    output = PACKET / 'matrix-v1'
    rows = [json.loads(line) for line in (output / 'raw.jsonl').read_bytes().splitlines()]
    original, descriptive = module('audit'), module('audit_v2')
    try:
        original.audit(output, rows)
    except ValueError as error:
        require(str(error) == 'peer alive at fault barrier', 'original exact first refusal')
    else:
        raise ValueError('original failed allocation retroactively accepted')
    first = load('FIRST_AUDIT_TOOL_RECEIPT.json')
    require(first['first_result']['value']['exit_code'] == 1, 'first audit exit retained')
    require(repair['original_verdict'] == 'FAIL_PREDECLARED_BASELINE_SURVIVAL', 'original verdict')
    actual, recorded = descriptive.audit(output, rows), load('AUDIT_V2.json')
    require(actual == {key: recorded[key] for key in actual}, 'full retained summary')
    require(actual['primary_exits'] == [1, 2, 1, 2, 1, 2, 0, 0], 'exact primary exits')
    require(actual['peer_exits'] == [0, 0, 0, 17, 0, 0, 0, 0], 'exact peer exits')
    require(actual['synthetic_effect_counts'] == [0, 1, 0, 1, 0, 1, 1, 1], 'synthetic effect roster')
    require(actual['baseline_peer_termination_cause'] == 'UNKNOWN', 'unobserved cause')
    require(actual['exit_journal_gap_cases'] == ['candidate-input-wrong-id'], 'historical receipt gap')
    require(len(recorded['controls']) == 8, 'copied control roster')
    for expected in recorded['controls']:
        require(expected['refused'] is True, 'recorded refusal')
        changed = [json.loads(line) for line in (PACKET / 'audit-controls-v2' / (expected['name'] + '.jsonl')).read_bytes().splitlines()]
        require(json.dumps(changed, sort_keys=True) != json.dumps(rows, sort_keys=True), 'effective typed corruption')
        try:
            descriptive.audit(output, changed)
        except ValueError as error:
            require(str(error) == expected['error'], 'exact corruption refusal')
        else:
            raise ValueError('copied corruption accepted')
    return {'disposition': 'PASS_ARCHIVE_RECONSTRUCTION_ONLY', 'original_verdict': actual['primary_question'],
            'rows': 8, 'controls_refused': 8, 'baseline_termination_cause': 'UNKNOWN',
            'original_audit_exit': 1, 'producer_reexecuted': False}


class ArchiveTests(unittest.TestCase):
    def test_complete_git_manifests_and_ten_source_images(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 261)
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT), path)
        for manifest_name, count in [('SHA256SUMS', 253), ('SHA256SUMS_V2', 260)]:
            manifest = {}
            for line in (PACKET / manifest_name).read_text().splitlines():
                digest, name = line.split('  ', 1)
                self.assertNotIn(name, manifest)
                manifest[name] = digest
            self.assertEqual(len(manifest), count)
            for name, digest in manifest.items():
                self.assertEqual(sha((PACKET / name).read_bytes()), digest, name)
            if manifest_name == 'SHA256SUMS_V2':
                self.assertEqual(set(manifest), {p[len(REL) + 1:] for p in paths} - {'SHA256SUMS_V2'})
        images = load('SOURCE.json')['images']
        self.assertEqual(len(images), 10)
        for item in images:
            data = (PACKET / 'source' / item['arm'] / Path(item['path']).name).read_bytes()
            self.assertEqual(data, subprocess.check_output(['git', 'show', item['commit'] + ':' + item['path']], cwd=ROOT))
            self.assertEqual(len(data), item['bytes'])
            self.assertEqual(sha(data), item['sha256'])
            self.assertEqual(subprocess.check_output(['git', 'rev-parse', item['commit'] + ':' + item['path']], cwd=ROOT).decode().strip(), item['blob'])

    def test_first_refusal_and_full_reconstruction_normal_and_optimized(self):
        for flags in (['-B'], ['-O', '-B']):
            actual = json.loads(subprocess.check_output([sys.executable, *flags, __file__, '--verify'], cwd=ROOT))
            self.assertEqual(actual, {'disposition': 'PASS_ARCHIVE_RECONSTRUCTION_ONLY',
                'original_verdict': 'FAIL_PREDECLARED_BASELINE_SURVIVAL', 'rows': 8,
                'controls_refused': 8, 'baseline_termination_cause': 'UNKNOWN',
                'original_audit_exit': 1, 'producer_reexecuted': False})


if __name__ == '__main__':
    if sys.argv[1:] == ['--verify']:
        print(json.dumps(retained_check(), sort_keys=True))
    else:
        unittest.main()
