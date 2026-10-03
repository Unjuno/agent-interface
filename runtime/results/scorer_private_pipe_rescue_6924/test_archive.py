"""Archive-only reconstruction: no candidate, OS-pipe deck or scheduler execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/doom/scorer_private_pipe_59_20261003_01a0ff52_93c2'
PACKET = ROOT / REL
SOURCE = '17af2d061012721bde0efd778c07cd9d1e8f2ea4'
RAW_SHA = 'd3dcb1d79b6f75f3f498b5ff4160bf08de62431e1af17a5c87ea68acda91af82'


def load(name):
    return json.loads((PACKET / name).read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ArchiveTests(unittest.TestCase):
    def test_complete_packet_source_freeze_and_stream_custody(self):
        entries = {}
        for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertNotIn(name, entries)
            entries[name] = digest
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 57)
        self.assertEqual(len(entries), 56)
        self.assertEqual(set(entries), {name[len(REL) + 1:] for name in paths} - {'SHA256SUMS'})
        for name in paths:
            data = (ROOT / name).read_bytes()
            self.assertEqual(data, subprocess.check_output(['git', 'show', SOURCE + ':' + name], cwd=ROOT), name)
            relative = name[len(REL) + 1:]
            if relative in entries:
                self.assertEqual(sha(data), entries[relative])
        freeze = load('FREEZE.json')
        self.assertEqual(len(freeze['inputs']), 17)
        for item in freeze['inputs']:
            data = (PACKET / item['path']).read_bytes()
            self.assertEqual(len(data), item['bytes'])
            self.assertEqual(sha(data), item['sha256'])
        pins = load('SOURCE.json')
        self.assertEqual(len(pins), 6)
        for item in pins:
            data = (PACKET / item['path']).read_bytes()
            self.assertEqual(len(data), item['bytes'])
            self.assertEqual(sha(data), item['sha256'])
            self.assertEqual(data, subprocess.check_output(['git', 'show', item['ref'] + ':' + item['repository_source']], cwd=ROOT))
        self.assertEqual(sha((PACKET / 'results/raw.jsonl').read_bytes()), RAW_SHA)
        publication = load('PUBLICATION.json')
        mappings = {item['path']: item for item in publication['files']}
        self.assertEqual(len(mappings), len(publication['files']))
        for name, item in mappings.items():
            self.assertEqual(sha((PACKET / name).read_bytes()), item['published_sha256'])
            self.assertIs(item['derivative'], item['original_sha256'] != item['published_sha256'])
        for name in paths:
            if not name.endswith('.receipt.json'):
                continue
            relative = name[len(REL) + 1:]
            receipt = load(relative)
            for stream in ('stdout', 'stderr'):
                target = relative.removesuffix('.receipt.json') + '.' + stream + '.log'
                self.assertEqual(receipt[stream + '_sha256'], mappings[target]['original_sha256'])
        self.assertEqual(load('development/audit-first-red.receipt.json')['exit_code'], 1)
        execution = load('results/EXECUTION.json')
        self.assertEqual([execution[key] for key in ('formal_producer_count', 'formal_auditor_count', 'formal_retries')], [1, 1, 0])

    def test_exact_retained_audit_and_twelve_corruptions_normal_and_optimized(self):
        for flags in (['-B'], ['-O', '-B']):
            with tempfile.TemporaryDirectory(prefix='pipe-6924-raw-only-') as temporary:
                out = Path(temporary)
                for helper, output in [('audit.py.txt', 'audit.json'), ('controls.py.txt', 'controls.json')]:
                    completed = subprocess.run([sys.executable, *flags, str(PACKET / helper),
                        str(PACKET / 'results/raw.jsonl'), str(out / output)], cwd=ROOT,
                        capture_output=True, check=True)
                    self.assertEqual(completed.stderr, b'')
                    actual, expected = json.loads((out / output).read_bytes()), load('results/' + output)
                    if output == 'controls.json':
                        # The oracle iterates a set of case fields. A reordered row can
                        # fail on any changed field first across hash seeds/interpreters.
                        rows = [json.loads(line) for line in (PACKET / 'results/raw.jsonl').read_text().splitlines()]
                        allowed = {'case field ' + key for key in
                            ('index', 'case_id', 'repetition', 'condition', 'variant', 'adapter')
                            if rows[0][key] != rows[1][key]}
                        for observed, historical in zip(actual['controls'], expected['controls']):
                            if observed['control'] == 'reordered_rows':
                                self.assertIn(observed['diagnostic'], allowed)
                                self.assertIn(historical['diagnostic'], allowed)
                                observed['diagnostic'] = historical['diagnostic']
                    self.assertEqual(actual, expected)
                controls = json.loads((out / 'controls.json').read_bytes())
                self.assertEqual(len(controls['controls']), 12)
                self.assertTrue(all(item['rejected'] is True for item in controls['controls']))
                audit = json.loads((out / 'audit.json').read_bytes())
                self.assertEqual(audit['rows'], 60)
                censored = [row for row in audit['results'] if row['censored']]
                self.assertEqual(len(censored), 16)
                self.assertTrue(all(row['variant'] == 'retained' and row['samples'] == 4
                    and row['readiness_to_command_ns'] is None for row in censored))
                self.assertEqual(sum(row['variant'] == 'v2' and not row['censored'] for row in audit['results']), 24)
                self.assertEqual(sum(row['variant'] == 'read_first' and row['samples'] == 0 for row in audit['results']), 12)

    def test_posthoc_terminal_accounting_counterevidence(self):
        rows = [json.loads(line) for line in (PACKET / 'results/raw.jsonl').read_text().splitlines()]
        actual = []
        for row in rows:
            if row['variant'] != 'v2' or row['condition'] == 'fast':
                continue
            receipt = row['receipts'][0]
            command = next(event['ns'] for event in row['events'] if event['kind'] == 'command_enter')
            actual.append({'case_id': row['case_id'], 'receipt_scheduled_ns': receipt['scheduled_ns'],
                'command_ns': command, 'period_ns': row['period_ns'],
                'complete_period_boundaries_after_scheduled_by_command': (command - receipt['scheduled_ns']) // row['period_ns'],
                'source_reported_missed_sample_periods': row['stats']['missed_sample_periods'],
                'sample_count': row['stats']['samples'], 'same_frozen_raw': True})
        recorded = load('POSTHOC.json')
        self.assertEqual(recorded['raw_sha256'], RAW_SHA)
        self.assertEqual(actual, recorded['results'])
        self.assertEqual(len(actual), 16)
        self.assertTrue(all(item['complete_period_boundaries_after_scheduled_by_command'] >= 2
            and item['source_reported_missed_sample_periods'] == 0 for item in actual))
        self.assertEqual(recorded['full_measurement_integration_status'], 'UNEXECUTED')
        self.assertEqual(recorded['runtime_adoption_review'], 'CHANGES; old approval withdrawn')


if __name__ == '__main__':
    unittest.main()
