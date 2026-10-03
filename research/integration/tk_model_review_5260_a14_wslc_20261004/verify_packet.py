"""Read-only first-H_FAIL preservation. Never invokes GUI, containers or models."""
from datetime import datetime
import json
from pathlib import Path, PurePosixPath
import re
from audit import inspect, process_errors, sha

ROOT = Path(__file__).resolve().parent
SOURCE = '0c2326209ad11f75046b643c958fba65856cd09b'
ALLOCATION = '5260-a14-wslc-model-review02-20261004'
FREEZE_SHA = '91339f436ce0501ce3c5c4f738f1e710efdde44a33e8d03ce4ca9870a301b1fd'
RAW_SHA = '392acfccb737608e80f516bfa59f8b1d0cf02d01defd37d944b80c26463fe605'
FIRST_SHA = 'd62845b0c781be6f712eb620ad2401c2a80bdfc8712a8f5033b76cba86f76c81'


def manifest_errors(root, lines):
    root = Path(root).resolve(); errors = []; seen = set()
    for line in lines:
        digest, separator, name = line.partition('  ')
        path_name = PurePosixPath(name)
        if (not separator or not re.fullmatch('[0-9a-f]{64}', digest)
                or not name or path_name.is_absolute() or '..' in path_name.parts
                or '\\' in name or ':' in name or name == 'SHA256SUMS'):
            errors.append('unsafe_manifest'); continue
        path = (root / name).resolve()
        if root not in path.parents:
            errors.append('escaping_manifest'); continue
        if name in seen:
            errors.append('duplicate_manifest')
        seen.add(name)
        try:
            if sha(path) != digest:
                errors.append('manifest_hash:' + name)
        except OSError:
            errors.append('manifest_missing:' + name)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and p.name != 'SHA256SUMS' and '__pycache__' not in p.parts}
    if actual != seen:
        errors.append('incomplete_manifest')
    return errors


def check_packet(root=ROOT):
    root = Path(root); errors = []
    try:
        errors.extend(manifest_errors(root, (root / 'SHA256SUMS').read_text().splitlines()))
        retained = root / 'retained'
        retention = json.loads((root / 'RETENTION.json').read_bytes())
        if retention['source_commit'] != SOURCE or retention['allocation'] != ALLOCATION:
            errors.append('retention_header')
        actual = {p.relative_to(retained).as_posix(): sha(p)
                  for p in retained.rglob('*') if p.is_file()}
        if actual != retention['original_files_sha256'] or len(actual) != 72:
            errors.append('original_evidence_bytes')
        freeze = json.loads((root / 'FREEZE.json').read_bytes())
        if sha(root / 'FREEZE.json') != FREEZE_SHA or freeze['allocation'] != ALLOCATION:
            errors.append('original_freeze')
        if len(freeze['sha256']) != 19:
            errors.append('frozen_source_coverage')
        for name, digest in freeze['sha256'].items():
            if sha(root / name) != digest:
                errors.append('frozen_source:' + name)
        inherited = json.loads((root / 'INHERITED.json').read_bytes())
        if len(inherited['unchanged_files_sha256']) != 11 or any(
                sha(root / name) != digest
                for name, digest in inherited['unchanged_files_sha256'].items()):
            errors.append('inherited_source')
        raw_path = retained / 'review01-candidate-data/candidate_stdout.json'
        if sha(raw_path) != RAW_SHA:
            errors.append('first_raw')
        first_path = retained / 'review01-auditor-launch/stdout.bin'
        first = json.loads(first_path.read_bytes())
        rebuilt = inspect(retained, root)
        if (sha(first_path) != FIRST_SHA or first != rebuilt
                or first['status'] != 'METHOD_PASS_FINITE_REVIEW_ONLY'
                or first['hypothesis'] != 'H_FAIL_FINITE_REVIEW_ONLY'
                or first['errors'] or len(first['observations']) != 4
                or [r['exact'] for r in first['observations']] != [True, False, True, True]):
            errors.append('first_h_fail_changed')
        binding = dict(source_commit=SOURCE, allocation=ALLOCATION,
                       freeze_sha256=FREEZE_SHA, source_sha256=freeze['sha256'])
        receipts = {}
        for role in ('candidate', 'model', 'auditor'):
            directory = retained / ('review01-' + role + '-launch')
            receipt = json.loads((directory / 'receipt.json').read_bytes())
            receipts[role] = receipt
            errors.extend(role + ':' + error for error in
                          process_errors(directory, receipt, freeze['commands'][role]))
            wanted = dict(binding)
            if role == 'auditor':
                wanted['candidate_raw_sha256'] = RAW_SHA
            if receipt['binding'] != wanted:
                errors.append(role + ':source_binding')
        if datetime.fromisoformat(receipts['model']['finished_utc']) > datetime.fromisoformat(receipts['auditor']['started_utc']):
            errors.append('auditor_phase_order')
        observations = first['observations']
        sums = {}
        for observation in observations:
            for name, value in observation['usage'].items():
                sums[name] = sums.get(name, 0) + value
        return dict(status='FAIL_RETAINED_PACKET' if errors else 'PASS_RETAINED_H_FAIL_ONLY',
                    errors=errors, original_status=first['status'],
                    original_hypothesis=first['hypothesis'], exact=[r['exact'] for r in observations],
                    model_requests_retained=4, usage_column_sums=sums,
                    container_gui_model_commands_executed=0)
    except (KeyError, TypeError, ValueError, OSError, IndexError, AttributeError) as exc:
        return dict(status='FAIL_RETAINED_PACKET', errors=errors + ['malformed:' + type(exc).__name__])


if __name__ == '__main__':
    result = check_packet()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(bool(result['errors']))
