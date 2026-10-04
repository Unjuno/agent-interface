"""Retained-data verification only; never run the native co-ready producer."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/concurrency/pipe_co_ready_6501_20261003_01a0ff52_5884'
PACKET = ROOT / REL
SOURCE = '6ad7cd2cf31480e615de80f4b2ffdba2665d6314'
RAW_SHA = '88f79f5c5e3eaec5420c16e3019c20b0f656b06e1cb080c4a1cc133fe4029578'


def load(name):
    return json.loads((PACKET / name).read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ArchiveTests(unittest.TestCase):
    def test_original_git_manifest_freeze_and_receipts(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 38)
        manifest = load('MANIFEST.json')['files']
        self.assertEqual(len(manifest), 37)
        self.assertEqual({item['path'] for item in manifest}, {p[len(REL) + 1:] for p in paths} - {'MANIFEST.json'})
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT))
        for item in manifest:
            data = (PACKET / item['path']).read_bytes()
            self.assertIs(type(item['bytes']), int)
            self.assertEqual(len(data), item['bytes'])
            self.assertEqual(sha(data), item['sha256'])
        attempt, freeze = load('run-01/attempt.json'), load('FREEZE.json')
        self.assertEqual(len(freeze['source_pins']), 12)
        for name, pin in freeze['source_pins'].items():
            data = (PACKET / name).read_bytes()
            self.assertEqual(data, subprocess.check_output(['git', 'show', attempt['source_commit'] + ':' + REL + '/' + name], cwd=ROOT))
            self.assertEqual(len(data), pin['bytes'])
            self.assertEqual(sha(data), pin['sha256'])
        self.assertEqual(sha((PACKET / 'FREEZE.json').read_bytes()), attempt['source_freeze_sha256'])
        self.assertEqual([attempt[key] for key in ('producer_invocations', 'primary_audit_invocations', 'formal_retries')], [1, 1, 0])
        for receipt in attempt['commands']:
            self.assertEqual(receipt['exit_code'], 0)
            for stream in ('stdout', 'stderr'):
                self.assertEqual(sha((PACKET / 'run-01' / (receipt['name'] + '.' + stream + '.txt')).read_bytes()), receipt[stream + '_sha256'])
        self.assertEqual(sha((PACKET / 'run-01/raw.jsonl').read_bytes()), RAW_SHA)
        self.assertEqual(len((PACKET / 'run-01/raw.jsonl').read_bytes()), 81594)
        checks = load('local-checks/receipts.json')
        self.assertEqual([item['exit_code'] for item in checks], [0, 2, 0])
        for receipt in checks:
            for stream in ('stdout', 'stderr'):
                self.assertEqual(sha((PACKET / 'local-checks' / (receipt['name'] + '.' + stream + '.txt')).read_bytes()), receipt[stream + '_sha256'])

    def test_full_raw_audit_and_effective_controls_normal_and_optimized(self):
        original = (PACKET / 'run-01/raw.jsonl').read_bytes()
        records = [json.loads(line) for line in original.splitlines()]
        controls = load('copied-controls/summary.json')
        self.assertEqual(len(controls['outcomes']), 8)
        self.assertEqual(controls['original_sha256_before'], RAW_SHA)
        self.assertEqual(controls['original_sha256_after'], RAW_SHA)
        for expected in controls['outcomes']:
            changed = copy.deepcopy(records)
            events = changed[1]['events']
            def event(kind, purpose=None):
                return next(e for e in events if e['kind'] == kind and (purpose is None or e.get('purpose') == purpose))
            name = expected['name']
            if name == 'boolean_fd':
                events[0]['fd'] = True
            elif name == 'boolean_count':
                event('write_return')['count'] = True
            elif name == 'primary_wrong_byte':
                event('read_return', 'primary')['hex'] = '58'
            elif name == 'hidden_control_ready':
                event('poll_return')['ready'] = [e for e in event('poll_return')['ready'] if e['resource'] != 'control']
            elif name == 'missing_row':
                del changed[2]
            elif name == 'cleanup_relabelled_primary':
                event('read_return', 'cleanup')['purpose'] = 'primary'
            elif name == 'poll_before_write':
                poll = next(i for i, e in enumerate(events) if e['kind'] == 'poll_requested')
                write = next(i for i, e in enumerate(events) if e['kind'] == 'write_requested')
                events[poll]['kind'], events[write]['kind'] = events[write]['kind'], events[poll]['kind']
            elif name == 'unclosed_fd':
                event('close_checked')['open'] = True
            else:
                self.fail('unknown copied control')
            data = b''.join((json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n').encode() for row in changed)
            self.assertNotEqual(data, original)
            self.assertEqual(data, (PACKET / 'copied-controls' / (name + '.jsonl')).read_bytes())
            self.assertEqual(sha(data), expected['sha256'])
        for flags in (['-B'], ['-O', '-B']):
            with tempfile.TemporaryDirectory(prefix='co-ready-6927-raw-only-') as temporary:
                output = Path(temporary)
                completed = subprocess.run([sys.executable, *flags, str(PACKET / 'audit.py.txt'),
                    str(PACKET / 'run-01/raw.jsonl'), str(output / 'baseline.json')], capture_output=True, check=True, cwd=ROOT)
                self.assertEqual(completed.stderr, b'')
                self.assertEqual(json.loads((output / 'baseline.json').read_bytes()), load('run-01/audit.json'))
                for expected in controls['outcomes']:
                    target = output / (expected['name'] + '.json')
                    rejected = subprocess.run([sys.executable, *flags, str(PACKET / 'audit.py.txt'),
                        str(PACKET / 'copied-controls' / (expected['name'] + '.jsonl')), str(target)],
                        capture_output=True, cwd=ROOT)
                    self.assertEqual(rejected.returncode, 1)
                    self.assertFalse(target.exists())
                    self.assertEqual(rejected.stdout, b'')
                    self.assertEqual(rejected.stderr.decode().splitlines()[-1], 'ValueError: ' + expected['reason'])

    def test_independent_cancellation_priority_truth_table(self):
        records = [json.loads(line) for line in (PACKET / 'run-01/raw.jsonl').read_bytes().splitlines()]
        self.assertEqual(len(records), 22)
        deck = load('INPUT.json')
        violations = []
        both = {'first_ready': 0, 'control_priority': 0}
        for row, case in zip(records[1:-1], deck):
            self.assertEqual(row['case'], case)
            events = row['events']
            ready = next(e['ready'] for e in events if e['kind'] == 'poll_return')
            names = [entry['resource'] for entry in ready]
            primary = next(e['resource'] for e in events if e['kind'] == 'selected')
            reads = [e for e in events if e['kind'] == 'read_return' and e.get('purpose') == 'primary']
            expected = 'control' if 'control' in names else 'data' if 'data' in names else None
            if case['condition'] == 'both':
                both[case['policy']] += 1
                self.assertEqual(names, case['write_order'])  # historical deck observation only
            if case['policy'] == 'control_priority':
                self.assertEqual(primary, expected)
            if primary != expected:
                self.assertEqual(case['policy'], 'first_ready')
                self.assertEqual(case['condition'], 'both')
                violations.append(case['trial_id'])
            self.assertEqual(len(reads), int(primary is not None))
            if reads:
                self.assertEqual(reads[0]['resource'], primary)
                self.assertEqual(reads[0]['hex'], {'control': '43', 'data': '44'}[primary])
            closes = [e for e in events if e['kind'] == 'close_checked']
            self.assertEqual(len(closes), 5)
            self.assertTrue(all(e['open'] is False for e in closes))
        self.assertEqual(both, {'first_ready': 4, 'control_priority': 4})
        self.assertEqual(violations, ['C001', 'C006'])


if __name__ == '__main__':
    unittest.main()
