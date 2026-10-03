"""Verify retained bytes, exits, raw oracle results and mutation witnesses."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def require(value, reason):
    if not value: raise ValueError(reason)

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    freeze = json.loads((ROOT / 'FREEZE.json').read_text())
    for name, record in freeze['files'].items():
        data = (ROOT / name).read_bytes()
        require(len(data) == record['bytes'] and sha(data) == record['sha256'], f'freeze: {name}')
    v2 = json.loads((ROOT / 'CONTROL_FREEZE_V2.json').read_text())
    require(sha((ROOT / 'controls_v2.py').read_bytes()) == v2['new_control_sha256'], 'v2 control source')
    publication = json.loads((ROOT / 'LOG_PUBLICATION.json').read_text())
    derivatives = {r['path']: r for r in publication['redactions']}
    receipts = list((ROOT / 'execution').glob('*/receipt.json'))
    for file in receipts:
        receipt = json.loads(file.read_text())
        expected_exit = {'controls': 1, 'workspace-base': 2}.get(file.parent.name, 0)
        require(receipt['returncode'] == expected_exit, f'exit: {file.parent.name}')
        for channel, record in receipt['logs'].items():
            log = file.parent / f'{channel}.txt'
            relative = log.relative_to(ROOT).as_posix()
            if relative in derivatives:
                derivative = derivatives[relative]
                require(record['sha256'] == derivative['original_sha256'], 'original log identity')
                require(sha(log.read_bytes()) == derivative['published_sha256'], 'public derivative identity')
            else:
                require(sha(log.read_bytes()) == record['sha256'], f'log: {relative}')
    spec = importlib.util.spec_from_file_location('verify_raw_oracle', ROOT / 'auditor.py')
    oracle = importlib.util.module_from_spec(spec); spec.loader.exec_module(oracle)
    summaries = {}
    for arm in ('baseline', 'combined'):
        raw = ROOT / 'evidence' / f'{arm}.jsonl'
        rows = [json.loads(line) for line in raw.read_text().splitlines()]
        result = oracle.check(rows, arm)
        recorded = json.loads((ROOT / 'execution' / f'audit-{arm}' / 'stdout.txt').read_text())
        require(all(recorded[k] == v for k, v in result.items()), f'raw audit reproduction: {arm}')
        require(recorded['raw_sha256'] == sha(raw.read_bytes()), f'raw hash: {arm}')
        require(not result['errors'], f'evidence errors: {arm}')
        if arm == 'combined': require(result['mismatch_count'] == 0, 'combined mismatch')
        summaries[arm] = {k: result[k] for k in ('rows', 'mismatch_count', 'execution_entries', 'successes')}
    controls = json.loads((ROOT / 'evidence/controls-v2.json').read_text())
    require(controls['all_effective'] is True and len(controls['implementation_controls']) == 7
            and len(controls['raw_controls']) == 7, 'complete controls')
    control_by_name = {r['control']: r for r in controls['implementation_controls']}
    retention = json.loads((ROOT / 'DELETION_RETENTION.json').read_text())
    require(len(retention) == 9, 'deletion raw retention')
    for record in retention:
        archive = (ROOT / record['file']).read_bytes()
        require(sha(archive) == record['gzip_sha256'], 'gzip binding')
        raw = gzip.decompress(archive)
        require(len(raw) == record['raw_bytes'] and sha(raw) == record['raw_sha256'], 'gzip readback')
        if record['version'] == 'v2':
            control = control_by_name[record['control']]
            require(control['raw_sha256'] == sha(raw), 'control raw identity')
            rows = [json.loads(line) for line in raw.decode().splitlines()]
            result = oracle.check(rows, 'combined')
            require(result['errors'] == control['errors'] and result['mismatch_count'] == control['mismatch_count'],
                    'deleted-guard evidence')
            require(result['mismatch_count'] > 0, 'undetected guard deletion')
            source_name = 'compiled_gui.py' if record['control'] == 'compiled-sequence' else 'contract.py'
            source = ROOT / Path(record['file']).parent / source_name
            require(sha(source.read_bytes()) == control['source_sha256'], 'mutated source identity')
    require(sum((ROOT / 'evidence' / f'{arm}.jsonl').stat().st_size for arm in ('baseline', 'combined')) < 32 * 1024**2,
            'baseline/combined output bound')
    require(sum(r['raw_bytes'] for r in retention if r['version'] == 'v2') < 128 * 1024**2, 'control output bound')
    print(json.dumps({'disposition': 'PASS_CORE_BOUNDARY_CONJUNCTION_SCOPED',
        'freeze_files': len(freeze['files']), 'execution_receipts': len(receipts),
        'retained_deletion_raw': len(retention), 'arms': summaries}, sort_keys=True))

if __name__ == '__main__': main()
