"""Recheck retained JSON only; never run native collector or auditor CLI."""
import argparse
import copy
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / 'research/concurrency/cancel_wake_saturation_17_20261003_01a0ff52'
EXPECTED_FIRST = '1d69a35be425e7f996c3f5a0ab6e8aaad3d242410c0fd40c45741c4d7a02e9f8'


def verify():
    checked = 0
    for line in (PACKET / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected, name = line.split(None, 1)
        path = (PACKET / name).resolve()
        if not path.is_relative_to(PACKET.resolve()):
            raise ValueError('manifest path escaped packet')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('manifest mismatch: ' + name)
        checked += 1
    if checked != 213:
        raise ValueError('original manifest entry count changed')

    source = PACKET / 'audit.py.txt'
    # The complete saved-only module was reviewed. It imports only stdlib data
    # helpers; its guarded CLI is suppressed. No driver/control module is loaded.
    namespace = {'__name__': 'retained_wake_saved_only', '__file__': str(source)}
    exec(compile(source.read_bytes(), str(source), 'exec'), namespace)
    raw, first = namespace['load'](PACKET / 'results/native/FIRST.json')
    input_raw, inputs = namespace['load'](PACKET / 'INPUTS.json')
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIRST:
        raise ValueError('first-outcome raw hash changed')
    freeze_raw = (PACKET / 'FREEZE.json').read_bytes()
    if first['freeze_sha256'] != hashlib.sha256(freeze_raw).hexdigest():
        raise ValueError('raw does not bind original freeze')
    freeze = json.loads(freeze_raw)
    for name, expected in freeze['source_sha256'].items():
        if hashlib.sha256((PACKET / name).read_bytes()).hexdigest() != expected:
            raise ValueError('original frozen source mismatch: ' + name)

    disposition, reasons, rows = namespace['audit'](first, inputs, input_raw)
    if disposition != 'PASS_SCOPED_WAKE_PIPE_SATURATION' or reasons or len(rows) != 18:
        raise ValueError('retained evidence did not qualify')
    for i, row in enumerate(first['rows'], 1):
        individual = json.loads((PACKET / ('results/native/wake-%02d.json' % i)).read_bytes())
        if individual != row:
            raise ValueError('individual/aggregate row mismatch')

    corruptions = [
        lambda x: x['rows'][1].__setitem__('case', copy.deepcopy(x['rows'][0]['case'])),
        lambda x: x['rows'][0]['events'][0].__setitem__('ns', x['rows'][0]['end_ns'] + 1),
        lambda x: x['rows'][0]['joins'].__setitem__('sender', False),
        lambda x: x.__setitem__('inputs_sha256', '0' * 64),
    ]
    for mutate in corruptions:
        changed = copy.deepcopy(first)
        mutate(changed)
        try:
            namespace['audit'](changed, inputs, input_raw)
        except namespace['Invalid']:
            continue
        raise ValueError('saved-data mutation accepted')

    return {'scope': 'SAVED_JSON_CONSISTENCY_ONLY', 'disposition': disposition,
            'manifest_targets': checked, 'qualified_rows': len(rows),
            'individual_rows_match': 18, 'mutation_controls_rejected': len(corruptions),
            'first_sha256': hashlib.sha256(raw).hexdigest(),
            'freeze_sha256': hashlib.sha256(freeze_raw).hexdigest(),
            'saved_auditor_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'python': sys.version, 'platform': platform.platform(), 'optimized': sys.flags.optimize,
            'native_or_collector_invocations': 0, 'native_auditor_cli_invocations': 0,
            'gui_input_or_resource_operations': 0,
            'historical_native_auditor_pid_recorded': False,
            'physical_release_or_task_effect_proven': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('use a fresh output path')
    result = verify()
    with args.output.open('xb') as stream:
        stream.write((json.dumps(result, indent=2) + '\n').encode())
    print(result['disposition'], 'saved rows:', result['qualified_rows'],
          'manifest:', result['manifest_targets'], 'mutations:', result['mutation_controls_rejected'])


if __name__ == '__main__':
    main()
