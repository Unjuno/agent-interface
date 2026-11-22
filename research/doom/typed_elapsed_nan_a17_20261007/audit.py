"""Read-only, separately implemented Decimal oracle; imports no study module."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
TOKENS = ('10', '10.0', '10.0000000005', '10.000000002', 'NaN',
          'Infinity', '-Infinity', 'null', 'true', '"10"', '[]', '{}')


def inspect(raw):
    errors = []
    def need(ok, message):
        if not ok:
            errors.append(message)
    need(raw.get('schema') == 'typed-elapsed-matrix-a17-v1', 'schema')
    need(raw.get('allocation') == 'a17-20261007-01', 'allocation')
    freeze = json.loads((ROOT / 'FREEZE.json').read_text())
    need(raw.get('source_sha256') == freeze['sha256'], 'source identity')
    for name, digest in freeze['sha256'].items():
        need(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, 'source bytes: ' + name)
    rows = raw.get('rows', [])
    expected = [(d, a, t) for d in ('default', 'strict') for a in (50, 200) for t in TOKENS]
    need(len(rows) == len(expected), 'denominator')
    for i, (row, (decoder, age, token)) in enumerate(zip(rows, expected)):
        tag = str(i) + ': '
        need(type(row.get('ordinal')) is int and row['ordinal'] == i, tag + 'ordinal')
        need((row.get('decoder'), row.get('age_ms'), row.get('token')) == (decoder, age, token), tag + 'schedule')
        wire = row.get('wire', '')
        need(hashlib.sha256(wire.encode()).hexdigest() == row.get('input_sha256'), tag + 'wire digest')
        packet = json.loads(wire, parse_float=Decimal, parse_int=Decimal, parse_constant=Decimal)
        value = packet['capture_to_typed_ready_ms']
        need(packet['capture_ns'] == Decimal(1_000_000_000) and
             packet['typed_extraction_started_ns'] == Decimal(1_001_000_000) and
             packet['typed_ready_ns'] == Decimal(1_010_000_000), tag + 'source clock')
        need(packet['sequence'] == Decimal(2) and packet['frame_size'] == [Decimal(640), Decimal(480)], tag + 'epoch/size')
        need(packet['event'] == 'typed_observation' and packet['schema'] == 'doom-typed-observation-v1'
             and packet['frame_rgb_sha256'] == 'a' * 64 and packet['artifact_published'] is False
             and packet['grants_input_authority'] is False, tag + 'packet identity')
        want_binding = {'focus': Decimal(7), 'surface': Decimal(7), 'geometry': [Decimal(x) for x in (0, 0, 640, 480)]}
        need(packet['pointer_binding'] == want_binding, tag + 'binding')
        for signal, v in (('health', 100), ('ammo', 50)):
            need(packet['signals'][signal] == {'signal_id': signal, 'sequence': Decimal(2),
                 'capture_ns': Decimal(1_000_000_000), 'binding': want_binding,
                 'status': 'observed', 'value': Decimal(v)}, tag + signal)
        expected_value = json.loads(token, parse_float=Decimal, parse_int=Decimal, parse_constant=Decimal)
        same_token = value.is_nan() and expected_value.is_nan() if isinstance(value, Decimal) and isinstance(expected_value, Decimal) and expected_value.is_nan() else value == expected_value
        need(same_token, tag + 'token value')
        nonstandard = token in ('NaN', 'Infinity', '-Infinity')
        rejected_decode = decoder == 'strict' and nonstandard
        need(row.get('decode') == ('rejected' if rejected_decode else 'accepted'), tag + 'decode')
        outcomes = row.get('outcomes', {})
        if rejected_decode:
            need(outcomes == {} and row.get('decoder_error') == 'ValueError', tag + 'decoder no call')
            continue
        need(set(outcomes) == {'original', 'candidate'}, tag + 'subject set')
        finite_consistent = (type(value) is Decimal and value.is_finite() and
                             abs(value - Decimal(10)) <= Decimal('0.000000001'))
        contract = row['contract']
        need(contract['max_current_age_ms'] == 100 and contract['source']['capture_ns'] == 900_000_000
             and contract['source']['sequence'] == 1 and contract['source']['binding'] == want_binding
             and contract['source']['signals'] == {'health': {'status': 'observed', 'value': 100}}
             and contract['predicates'] == [{'signal_id': 'health', 'operator': 'minimum', 'value': 90}], tag + 'contract')
        need(row['action'] == {'op': 'observe_only'}, tag + 'action')
        binding_hash = hashlib.sha256(json.dumps(row['action'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        need(contract['action_fingerprint'] == binding_hash and contract['format'] == 'action-validity-contract-v1', tag + 'contract identity')
        for name in ('original', 'candidate'):
            got = outcomes.get(name, {})
            accepts = finite_consistent or (name == 'original' and token == 'NaN')
            need(got.get('snapshot') == ('accepted' if accepts else 'rejected'), tag + name + ' snapshot')
            need(got.get('input_unchanged') is True, tag + name + ' input unchanged')
            if accepts:
                expected_snapshot = {'format': 'action-admission-snapshot-v1', 'sequence': 2,
                    'capture_ns': 1_000_000_000, 'binding': want_binding,
                    'signals': {'health': {'status': 'observed', 'value': 100}}}
                need(got.get('value') == expected_snapshot, tag + name + ' full snapshot')
                need(got.get('validity_status') == ('VALID_CURRENT' if age <= 100 else 'REJECTED_STALE'), tag + name + ' freshness')
                need(got.get('grants_input_authority') is False, tag + name + ' authority')
            else:
                need(got.get('error_type') == 'ValueError' and set(got) == {'snapshot', 'error_type', 'error', 'input_unchanged'}, tag + name + ' refusal')
    return errors


def main():
    raw = json.loads(Path(sys.argv[1]).read_text())
    errors = inspect(raw)
    controls = {}
    if '--controls' in sys.argv and not errors:
        def changed_status(x): x['rows'][4]['outcomes']['candidate']['snapshot'] = 'accepted'
        def authority(x): x['rows'][0]['outcomes']['original']['grants_input_authority'] = True
        def freshness(x): x['rows'][12]['outcomes']['candidate']['validity_status'] = 'VALID_CURRENT'
        def source(x): x['source_sha256']['run.py'] = '0' * 64
        def missing(x): x['rows'].pop()
        def wire(x): x['rows'][0]['wire'] = x['rows'][0]['wire'].replace('1000000000', '1000000001')
        for name, change in [('nan_accept', changed_status), ('authority', authority), ('stale_upgrade', freshness),
                             ('source', source), ('missing_row', missing), ('wire_change', wire)]:
            mutated = deepcopy(raw); change(mutated)
            if json.dumps(mutated, sort_keys=True) == json.dumps(raw, sort_keys=True):
                raise RuntimeError('no-op mutation: ' + name)
            controls[name] = bool(inspect(mutated))
        if not all(controls.values()): errors.append('mutation control failed')
    result = {'status': 'PASS_TYPED_ELAPSED_VALIDATION_SCOPED' if not errors else 'FAIL',
              'rows': len(raw.get('rows', [])), 'errors': errors, 'controls': controls}
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0 if not errors else 1

if __name__ == '__main__':
    raise SystemExit(main())
