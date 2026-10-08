"""Dated raw-only identity supplement; frozen v1 and all original bytes stay intact."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from audit import inspect, same


def identity_errors(raw):
    errors = []
    try:
        for index, row in enumerate(raw['rows']):
            cid = row['id']
            if type(row['display']) is not str or row['display'] != ':' + str(100 + index):
                errors.append(cid + '/display')
            if row['owner_ready']['role'] != 'owner' or row['consumer_ready']['role'] != 'consumer':
                errors.append(cid + '/ready-role')
            for item in row['signals']:
                if type(item['pid']) is not int or item['pid'] <= 0 or item['pid'] != row['pids']['owner']:
                    errors.append(cid + '/signal-pid-type')
    except Exception as error:
        errors.append('identity-unreadable:' + type(error).__name__ + ':' + str(error))
    return errors


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--raw', type=Path, required=True); parser.add_argument('--original-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    raw = json.loads(args.raw.read_text()); cases = json.loads(args.cases.read_text())['cases']
    errors = identity_errors(raw)
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / 'v1.json'
        p = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('audit.py')),
                            '--cases', str(args.cases), '--raw', str(args.raw), '--output', str(output)],
                           capture_output=True, timeout=15)
        base = json.loads(output.read_text())
    preserved = same(base, json.loads(args.original_audit.read_text()))
    if p.returncode != 0 or not preserved: errors.append('original-v1-reanalysis-mismatch')
    controls = []
    for name, kind, target in [('signal_pid_float', 'float', 'signal-pid-type'),
                               ('signal_pid_boolean', 'bool', 'signal-pid-type'),
                               ('display_unbound', 'display', 'display'),
                               ('display_alias', 'alias', 'display'),
                               ('owner_role_unbound', 'owner', 'ready-role'),
                               ('consumer_role_unbound', 'consumer', 'ready-role')]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'evidence'; shutil.copytree(args.raw.parent, root)
            changed = copy.deepcopy(raw); row = changed['rows'][4]
            if kind == 'float': row['signals'][0]['pid'] = float(row['pids']['owner'])
            elif kind == 'bool': row['signals'][0]['pid'] = True
            elif kind == 'display': row['display'] = ':999'
            elif kind == 'alias': row['display'] = ':103'
            elif kind == 'owner': row['owner_ready']['role'] = 'consumer'
            elif kind == 'consumer': row['consumer_ready']['role'] = 'owner'
            (root / row['id'] / 'row.json').write_text(json.dumps(row, indent=2) + '\n')
            old_errors, _ = inspect(changed, cases, root)
            new_errors = identity_errors(changed)
            named = row['id'] + '/' + target
            controls.append({'name': name, 'v1_rejected': bool(old_errors), 'v1_errors': old_errors,
                             'v2_target': named, 'v2_target_rejected': named in new_errors, 'v2_errors': new_errors})
            if named not in new_errors: errors.append('identity-control-not-rejected:' + name)
    result = {'status': 'PASS_RAW_IDENTITY_SUPPLEMENT_SCOPED' if not errors else 'FAIL_RAW_IDENTITY_SUPPLEMENT',
              'errors': errors, 'original_v1_reanalysis_equal': preserved,
              'original_control_count': len(base['controls']), 'additional_controls': controls,
              'raw_sha256': hashlib.sha256(args.raw.read_bytes()).hexdigest(), 'native_formal_replays': 0}
    with args.output.open('x') as stream: stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result)); raise SystemExit(bool(errors))


if __name__ == '__main__': main()
