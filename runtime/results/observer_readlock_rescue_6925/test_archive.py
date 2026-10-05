"""Retained-data checks only: never invoke producer or consumed audit entrypoints."""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/integration/observer_readlock_6526_20261003_01a0ff58'
PACKET = ROOT / REL
SOURCE = '2a34f9005eb79e87a7cbc276af639154dd91a7d6'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def load(name):
    return json.loads((PACKET / name).read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def retained_check():
    entries = load('SHA256SUMS.json')
    names = [entry['path'] for entry in entries]
    files = {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    require(len(names) == len(set(names)) == 74, 'unique manifest roster')
    require(set(names) == files - {'SHA256SUMS.json'}, 'complete packet roster')
    for entry in entries:
        data = (PACKET / entry['path']).read_bytes()
        require(type(entry['bytes']) is int and len(data) == entry['bytes'], 'manifest size')
        require(digest(data) == entry['sha256'], 'manifest hash')
    freeze, repair = load('freeze.json'), load('audit-v2-freeze.json')
    for name, expected in freeze['source_sha256'].items():
        require(digest((PACKET / name).read_bytes()) == expected, 'frozen source ' + name)
    for name, key in [('audit_v2.py', 'auditor_sha256'),
                      ('first/raw.jsonl', 'original_raw_sha256'),
                      ('freeze.json', 'original_freeze_sha256'),
                      ('custody/manifest.json', 'custody_manifest_sha256')]:
        require(digest((PACKET / name).read_bytes()) == repair[key], 'repair pin ' + name)
    publication = load('publication.json')
    derivatives = {item['path']: item for item in publication['derivatives']}
    require(len(derivatives) == len(publication['derivatives']), 'unique derivatives')
    for name, item in derivatives.items():
        require(digest((PACKET / name).read_bytes()) == item['published_sha256'], 'public derivative')
        require(item['path_redacted'] is (name == 'commands/audit/stderr.bin'), 'redaction roster')
        require((item['original_sha256'] != item['published_sha256']) is item['path_redacted'], 'projection identity')
    for item in load('validation.json')['derivatives']:
        require(item['path'] not in derivatives, 'separate collection projection')
        require(digest((PACKET / item['path']).read_bytes()) == item['published_sha256'], 'collection derivative')
        derivatives[item['path']] = item
    for command, exit_code in [('producer', 0), ('audit', 1), ('audit-v2', 0),
                               ('collect-only', 1), ('collect-only-v2', 5), ('construction', 0)]:
        receipt = load('commands/' + command + '/receipt.json')
        require(type(receipt['exit_code']) is int and receipt['exit_code'] == exit_code, 'historical exit')
        for stream in ('stdout', 'stderr'):
            name = 'commands/' + command + '/' + stream + '.bin'
            original = derivatives[name]['original_sha256'] if name in derivatives else digest((PACKET / name).read_bytes())
            require(receipt[stream + '_sha256'] == original, 'receipt original-stream binding')
    manifest, recorded = load('custody/manifest.json'), load('audit-v2.json')
    decoded = {}
    for entry in manifest['files']:
        name = entry['name']
        require(name == Path(name).name and '/' not in name and '\\' not in name, 'native name')
        data = base64.b64decode((PACKET / 'custody/native' / (name + '.b64')).read_bytes().strip(), validate=True)
        require(type(entry['bytes']) is int and len(data) == entry['bytes'], 'decoded size')
        require(digest(data) == entry['sha256'] and name not in decoded, 'decoded hash/uniqueness')
        decoded[name] = data
    require(len(decoded) == 32, 'complete native capsules')
    for item in publication['native_transport']:
        name = Path(item['path']).name.removesuffix('.b64')
        require(digest((PACKET / item['path']).read_bytes()) == item['transport_sha256'], 'transport hash')
        require(digest(decoded[name]) == item['decoded_sha256'] and len(decoded[name]) == item['decoded_bytes'], 'transport decode binding')
    rows = [json.loads(line) for line in (PACKET / 'first/raw.jsonl').read_text().splitlines()]
    require([{k: row[k] for k in ('id', 'journal', 'policy', 'desired')} for row in rows] == load('plan.json')['cases'], 'planned deck')
    spec = importlib.util.spec_from_file_location('retained_observer_audit', PACKET / 'audit_v2.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    with tempfile.TemporaryDirectory(prefix='observer-6925-retained-') as temporary:
        private = Path(temporary)
        (private / 'custody/native').mkdir(parents=True)
        (private / 'dbs').mkdir()
        for name, data in decoded.items():
            (private / 'custody/native' / name).write_bytes(data)
            (private / 'dbs' / name).write_bytes(data)
        audit.ROOT = private
        audit.validate_custody(manifest)
        summary = audit.check(rows, private, freeze)
        require(summary == {key: recorded[key] for key in summary}, 'recorded finite summary')
        controls = {
            'missing': lambda r: r.pop(),
            'duplicate': lambda r: r.__setitem__(1, copy.deepcopy(r[0])),
            'commit_flip': lambda r: r[6]['commit'].__setitem__('ok', True),
            'observer_sql_hidden': lambda r: r[6]['observer_sql'].remove('BEGIN'),
            'query_only_bool': lambda r: r[2]['observer_settings'].__setitem__('query_only', True),
            'endpoint_lie': lambda r: r[6]['scorer'].__setitem__('stdout', r[0]['scorer']['stdout']),
            'db_hash': lambda r: r[0].__setitem__('db_sha256_before_score', '0' * 64),
            'native_exit': lambda r: r[0]['scorer'].__setitem__('exit_code', 9)}
        require(list(controls) == repair['copied_raw_controls'], 'frozen corruption deck')
        for expected in recorded['copied_raw_controls']:
            changed = copy.deepcopy(rows)
            controls[expected['control']](changed)
            require(json.dumps(changed, sort_keys=True, allow_nan=False) !=
                    json.dumps(rows, sort_keys=True, allow_nan=False), 'effective typed corruption')
            try:
                audit.check(changed, private, freeze)
            except ValueError as error:
                require(str(error) == expected['rejected'], 'exact raw rejection')
            else:
                raise ValueError('raw corruption accepted')
        for expected in recorded['custody_controls']:
            changed = copy.deepcopy(manifest)
            label = expected['control']
            if label == 'missing_wal':
                changed['files'] = [x for x in changed['files'] if x['name'] != '12-wal-held_sham-a.db-wal']
            elif label == 'wrong_hash':
                changed['files'][0]['sha256'] = '0' * 64
            elif label == 'size_bool':
                changed['files'][0]['bytes'] = True
            else:
                raise ValueError('unknown custody control')
            try:
                audit.validate_custody(changed)
            except ValueError as error:
                require(str(error) == expected['rejected'], 'exact custody rejection')
            else:
                raise ValueError('custody corruption accepted')
        # Independent read of four main-file-only copies demonstrates why WAL custody matters.
        omitted = private / 'main-only'
        omitted.mkdir()
        for row in rows[12:]:
            path = omitted / Path(row['db']).name
            path.write_bytes(decoded[path.name])
            connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
            try:
                actual = connection.execute('SELECT task_id,value,revision FROM task').fetchall()
            finally:
                connection.close()
            require(actual == [(1, 'old', 0)], 'main-only omitted committed WAL state')
        audit.validate_custody(manifest)
    require(recorded['original_audit_exit'] == 1 and recorded['producer_reexecuted'] is False, 'original failure retained')
    require(recorded['sidecar_hash_time'] == 'post-first-audit only', 'late custody boundary')
    return {'disposition': 'PASS_RETAINED_ARCHIVE_ONLY', 'packet_files': 75,
            'native_capsules': 32, 'rows': 16, 'committed': 14, 'busy_and_rolled_back': 2,
            'stale_wal_target_snapshots': 2, 'raw_controls': 8, 'custody_controls': 3,
            'main_only_omission_witnesses': 4, 'original_audit_exit': 1,
            'producer_reexecuted': False}


class ArchiveTests(unittest.TestCase):
    def test_original_git_blobs_and_prospective_source(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 75)
        for name in paths:
            self.assertEqual((ROOT / name).read_bytes(), subprocess.check_output(['git', 'show', SOURCE + ':' + name], cwd=ROOT), name)
        publication = load('source-publication.json')
        self.assertEqual(len(publication['additive_paths']), 16)
        for item in publication['additive_paths']:
            data = subprocess.check_output(['git', 'show', publication['source_head'] + ':' + item['path']], cwd=ROOT)
            self.assertEqual(data, (ROOT / item['path']).read_bytes())
            self.assertEqual(digest(data), item['sha256'])
            self.assertEqual(subprocess.check_output(['git', 'rev-parse', publication['source_head'] + ':' + item['path']], cwd=ROOT).decode().strip(), item['git_blob'])

    def test_retained_db_and_controls_normal_and_optimized(self):
        for flags in (['-B'], ['-O', '-B']):
            result = json.loads(subprocess.check_output([sys.executable, *flags, __file__, '--verify'], cwd=ROOT))
            self.assertEqual(result, {'disposition': 'PASS_RETAINED_ARCHIVE_ONLY', 'packet_files': 75,
                'native_capsules': 32, 'rows': 16, 'committed': 14, 'busy_and_rolled_back': 2,
                'stale_wal_target_snapshots': 2, 'raw_controls': 8, 'custody_controls': 3,
                'main_only_omission_witnesses': 4, 'original_audit_exit': 1, 'producer_reexecuted': False})


if __name__ == '__main__':
    if sys.argv[1:] == ['--verify']:
        print(json.dumps(retained_check(), sort_keys=True))
    else:
        unittest.main()
