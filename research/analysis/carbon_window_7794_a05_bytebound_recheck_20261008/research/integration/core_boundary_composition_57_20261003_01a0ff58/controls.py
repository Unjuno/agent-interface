"""Directed implementation deletion and internally rehashed raw controls."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('raw_oracle', ROOT / 'auditor.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=False)
    rows = [json.loads(line) for line in (ROOT / 'evidence' / 'combined.jsonl').read_text().splitlines()]
    assert not oracle.check(rows, 'combined')['errors']
    assert not oracle.check(rows, 'combined')['mismatch_count']
    positive = next(i for i, row in enumerate(rows) if row['terminal'] and row['terminal']['outcome'] == 'TASK_SUCCEEDED')
    negative = next(i for i, row in enumerate(rows) if row['case']['manifest'] == 'valid' and row['case']['now'] == 'zero'
                    and row['case']['observation'] == 'match' and row['case']['binding'] == 'match'
                    and row['case']['compiled_sequence'] == 'bool')
    raw_controls = []
    variants = {}
    changed = copy.deepcopy(rows); changed.pop(); variants['missing-row'] = changed
    changed = copy.deepcopy(rows); changed[1] = copy.deepcopy(changed[0]); variants['duplicate-row'] = changed
    changed = copy.deepcopy(rows); changed[positive]['trace'] = [e for e in changed[positive]['trace'] if e['call'] != 'execute']; variants['deleted-execute'] = changed
    changed = copy.deepcopy(rows); changed[negative]['exception'] = None; variants['missing-refusal'] = changed
    changed = copy.deepcopy(rows); changed[positive]['core_admission']['accepted'] = 1; variants['bool-to-int'] = changed
    changed = copy.deepcopy(rows)
    changed[positive]['input_before']['program']['source']['observation_seq'] = True
    changed[positive]['input_after'] = copy.deepcopy(changed[positive]['input_before'])
    for key in ('before', 'after'):
        changed[positive][f'input_{key}_sha256'] = oracle.canonical_hash(changed[positive][f'input_{key}'])
    variants['internally-rehashed-input'] = changed
    changed = copy.deepcopy(rows)
    for event in changed[positive]['journal']:
        if event['event'] == 'action_terminal': event['release_verified'] = 1
    variants['release-type'] = changed
    for name, copied_rows in variants.items():
        result = oracle.check(copied_rows, 'combined')
        rejected = bool(result['errors'] or result['mismatch_count'])
        raw_controls.append({'control': name, 'rejected': rejected, 'errors': result['errors'],
                             'mismatch_count': result['mismatch_count']})

    edits = {
        'manifest-os': ('contract.py', 'isinstance(platform.get("os"), str) and ', ''),
        'manifest-state': ('contract.py', 'isinstance(row.get("state"), str) and ', ''),
        'manifest-frame': ('contract.py', '    _need(all(isinstance(frame, str) for frame in frames), "coordinate_frames must contain strings")\n', ''),
        'current-now': ('contract.py', '        _bounded_int(now_ns, "now_ns", 0, 2**63 - 1)\n', ''),
        'current-observation': ('contract.py', '        _bounded_int(current_observation_seq, "current_observation_seq", 0, 2**63 - 1)\n', ''),
        'current-binding': ('contract.py', '        _bounded_int(current_binding_revision, "current_binding_revision", 0, 2**63 - 1)\n', ''),
        'compiled-sequence': ('compiled_gui.py', '                type(admission["expected_sequence"]) is not int or\n', ''),
    }
    implementation_controls = []
    for name, (filename, old, new) in edits.items():
        source = args.scratch / name / 'source'
        shutil.copytree(ROOT / 'source' / 'combined', source)
        target = source / 'runtime' / 'core_v1' / filename
        original = target.read_bytes()
        needle = old.encode()
        assert original.count(needle) == 1, name
        target.write_bytes(original.replace(needle, new.encode()))
        raw = args.scratch / name / 'raw.jsonl'
        command = [sys.executable, '-B', str(ROOT / 'runner.py'), '--arm', 'combined',
                   '--source', str(source), '--output', str(raw)]
        process = subprocess.run(command, capture_output=True, text=True)
        if process.returncode:
            raise RuntimeError(f'{name}: runner failed: {process.stderr}')
        mutant_rows = [json.loads(line) for line in raw.read_text().splitlines()]
        result = oracle.check(mutant_rows, 'combined')
        witness = result['mismatches'][0]['case_id'] if result['mismatches'] else None
        implementation_controls.append({'control': name, 'rows': len(mutant_rows),
            'returncode': process.returncode, 'source_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'raw_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(), 'errors': result['errors'],
            'mismatch_count': result['mismatch_count'], 'detected': bool(result['errors'] or result['mismatch_count']),
            'first_witness': next((row for row in mutant_rows if row['case']['case_id'] == witness), None)})
    result = {'raw_controls': raw_controls, 'implementation_controls': implementation_controls,
        'all_effective': all(r['rejected'] for r in raw_controls) and all(r['detected'] for r in implementation_controls)}
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'raw_controls': len(raw_controls), 'implementation_controls': len(implementation_controls),
                      'all_effective': result['all_effective']}))
    return 0 if result['all_effective'] else 1

if __name__ == '__main__': raise SystemExit(main())
