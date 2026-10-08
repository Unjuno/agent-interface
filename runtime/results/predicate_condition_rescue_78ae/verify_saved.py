"""Run the unchanged data-only checker; never execute experiment sources."""
from pathlib import Path
import hashlib
import json
import runpy
import shutil
import tarfile
import tempfile

root = Path(__file__).resolve().parents[3]
packet = root / 'research/live_control/appserver_predicate_condition_17_20261003_01a0ff52_b64b'
checksums = (packet / 'SHA256SUMS').read_text().splitlines()
for row in checksums:
    digest, name = row.split('  ', 1)
    if hashlib.sha256((packet / name).read_bytes()).hexdigest() != digest:
        raise ValueError('packet hash: ' + name)
checker = runpy.run_path(str(packet / 'check_saved.py.txt'), run_name='saved_only')
with tempfile.TemporaryDirectory(prefix='predicate-rescue-') as scratch:
    source = Path(scratch) / 'source'
    source.mkdir()
    for name in checker['REVIEWED']:
        shutil.copyfile(packet / (name + '.txt'), source / name)
    green = checker['check'](packet / 'raw', source, checker['REVIEWED'])
    copied = Path(scratch) / 'copied'
    copied.mkdir()
    with tarfile.open(packet / 'copied-controls-data.tar.gz', 'r:gz') as archive:
        archive.extractall(copied, filter='data')
    inventory = json.loads((packet / 'copied-controls-inventory.json').read_bytes())
    actual = {str(p.relative_to(copied)) for p in copied.rglob('*') if p.is_file()}
    if actual != set(inventory):
        raise ValueError('copy inventory paths')
    for name, row in inventory.items():
        data = (copied / name).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('copy hash: ' + name)
    refusals = []
    for row in json.loads((packet / 'copied-controls-result.json').read_bytes())['controls']:
        try:
            checker['check'](copied / row['control'], source, checker['REVIEWED'])
        except checker['Rejected'] as error:
            if str(error) != row['reason']:
                raise ValueError('changed refusal: ' + row['control']) from error
            refusals.append({'control': row['control'], 'reason': str(error)})
        else:
            raise ValueError('accepted corrupt copy: ' + row['control'])
    print(json.dumps({'status': 'PASS', 'packet_hashes': len(checksums),
                      'copied_inventory': len(inventory), 'green': green,
                      'refusals': refusals, 'experiment_source_imports': 0,
                      'native_replays': 0}, sort_keys=True, indent=2))
