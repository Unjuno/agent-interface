"""Saved native ledger reconstruction only; never run candidate/launch_once."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/concurrency/fd_lifetime_6501_20261003_01a0ff52'
PACKET = ROOT / REL
SOURCE = 'bfb0306f69976c3c78fa2b790844934b1eaa876a'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(name):
    return json.loads((PACKET / name).read_bytes())

class ArchiveTests(unittest.TestCase):
    def test_original_git_manifest_freeze_and_seven_tar_members(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 53)
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT))
        manifest = {}
        for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertNotIn(name, manifest)
            manifest[name] = digest
            self.assertEqual(sha((PACKET / name).read_bytes()), digest)
        self.assertEqual(set(manifest), {p[len(REL) + 1:] for p in paths} - {'SHA256SUMS'})
        freeze = load('FREEZE.json')['source_sha256']
        self.assertEqual(len(freeze), 20)
        for name, digest in freeze.items():
            self.assertEqual(sha((PACKET / name).read_bytes()), digest)
        custody = load('results/CUSTODY.json')
        with tarfile.open(PACKET / 'results/guest_output.tar', 'r') as archive:
            members = archive.getmembers()
            self.assertEqual(len(members), 8)
            self.assertEqual([(member.name, member.isdir()) for member in members if not member.isfile()], [('.', True)])
            files = [member for member in members if member.isfile()]
            self.assertEqual({member.name for member in files}, {'./' + item['name'] for item in custody['guest_original_members_verified']})
            for item in custody['guest_original_members_verified']:
                member = archive.getmember('./' + item['name'])
                self.assertTrue(member.isfile())
                data = archive.extractfile(member).read()
                self.assertEqual((len(data), sha(data)), (item['bytes'], item['sha256']))
                # Some public process receipts are path-projected; tar retains originals.
                if item['name'] != 'driver_receipts.json':
                    self.assertEqual(data, (PACKET / 'results' / item['name']).read_bytes())

    def test_full_saved_ledger_and_eight_copied_controls(self):
        spec = importlib.util.spec_from_file_location('retained_fd_audit', PACKET / 'audit.py')
        auditor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auditor)
        raw = (PACKET / 'results/raw.jsonl').read_bytes()
        records = [auditor.parse_line(line) for line in raw.splitlines()]
        actual = auditor.audit_records(records)
        recorded = load('results/audit.json')
        self.assertEqual(actual, {key: recorded[key] for key in actual})
        self.assertEqual((actual['rows'], actual['events'], actual['integer_replacement_failures'], actual['once_owner_replacement_failures']), (6, 134, 2, 0))
        self.assertEqual(sha(raw), recorded['raw_sha256'])
        summary = load('results/copied-controls/summary.json')
        self.assertEqual(len(summary['controls']), 8)
        for item in summary['controls']:
            data = (PACKET / ('results/copied-controls/' + item['name'] + '.json')).read_bytes()
            self.assertEqual(sha(data), item['sha256'])
            changed = auditor.parse_line(data)
            self.assertNotEqual(json.dumps(changed, sort_keys=True), json.dumps(records, sort_keys=True))
            with self.assertRaises((ValueError, KeyError, TypeError, IndexError)) as error:
                auditor.audit_records(changed)
            self.assertEqual(str(error.exception), item['rejection'])

if __name__ == '__main__':
    unittest.main()
