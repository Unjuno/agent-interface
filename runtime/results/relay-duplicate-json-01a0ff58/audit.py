"""Finite authored raw-only oracle; imports no relay, probe or MCP implementation."""
import copy
import hashlib
import json
from pathlib import Path


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def same(actual, expected):
    return json.dumps(actual, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(
        expected, sort_keys=True, separators=(',', ':'), allow_nan=False)


def accepted(response):
    require(type(response) is dict and set(response) == {
        'id','next_id','result','sdk_entry_ns','sdk_return_ns','status','tool'}, 'returned_schema')
    require(type(response['id']) is int and response['id'] == 1, 'accepted_id')
    require(type(response['next_id']) is int and response['next_id'] == 2, 'accepted_next_id')
    require(response['status'] == 'returned' and response['tool'] == 'interface_dispatch', 'accepted_identity')
    require(same(response['result'], {'content':[], 'isError':False, 'meta':None, 'structuredContent':None}), 'sdk_result')
    require(type(response['sdk_entry_ns']) is int and type(response['sdk_return_ns']) is int
            and 0 <= response['sdk_entry_ns'] <= response['sdk_return_ns'], 'sdk_interval')


def refused(response, next_id):
    require(type(response) is dict and set(response) == {'status','dispatched','next_id','error'}, 'refused_schema')
    require(response['status'] == 'refused' and response['dispatched'] is False, 'false_refusal')
    require(type(response['next_id']) is int and response['next_id'] == next_id, 'refused_next_id')
    require(type(response['error']) is str and len(response['error']) > 0, 'refusal_reason')


def check(raw, cases, sources, cases_hash):
    require(raw['schema'] == 'relay-duplicate-json-construction-v1', 'schema')
    require(raw['sources'] == sources, 'source_binding')
    require(raw['cases_sha256'] == cases_hash, 'cases_binding')
    require(raw['mcp'] == '1.30.0', 'sdk_binding')
    require(type(cases) is list and len(cases) == 16, 'oracle_denominator')
    by_name = {case['name']: case for case in cases}
    require(len(by_name) == 16 and sum(case['duplicate'] is True for case in cases) == 8, 'oracle_cases')
    require(type(raw['rows']) is list and len(raw['rows']) == 32, 'row_denominator')
    seen = set()
    for row in raw['rows']:
        require(type(row) is dict and set(row) == {'variant','case','line','response','initial_calls',
                'initial_call_count','same_id_followup','final_calls','final_call_count'}, 'row_schema')
        require(type(row['variant']) is str and type(row['case']) is str, 'row_identity_type')
        pair = row['variant'], row['case']
        require(row['variant'] in ('baseline','candidate') and row['case'] in by_name and pair not in seen,
                'row_identity')
        seen.add(pair)
        case = by_name[row['case']]
        require(type(case['duplicate']) is bool and row['line'] == case['line'], 'input_binding')
        require(type(row['initial_call_count']) is int and type(row['final_call_count']) is int, 'call_count_type')
        require(type(row['initial_calls']) is list and type(row['final_calls']) is list, 'call_list_type')
        blocked = row['variant'] == 'candidate' and case['duplicate']
        if blocked:
            refused(row['response'], 1)
            require(row['initial_call_count'] == 0 and row['initial_calls'] == [], 'dispatch_before_refusal')
            accepted(row['same_id_followup'])
            expected_final = [{'tool':'interface_dispatch','arguments':{}}]
        else:
            accepted(row['response'])
            expected_final = [{'tool':'interface_dispatch','arguments':case['expected_arguments']}]
            require(row['initial_call_count'] == 1 and same(row['initial_calls'], expected_final), 'forwarded_arguments')
            refused(row['same_id_followup'], 2)
        require(row['final_call_count'] == 1 and same(row['final_calls'], expected_final), 'no_replay_and_followup')
    require(seen == {(variant, name) for variant in ('baseline','candidate') for name in by_name}, 'coverage')


def main():
    root = Path(__file__).resolve().parent
    raw = json.loads((root / 'raw.json').read_bytes())
    cases_bytes = (root / 'cases.json').read_bytes()
    cases = json.loads(cases_bytes)
    sources = json.loads((root / 'SOURCE.json').read_bytes())['sources']
    for name, expected in sources.items():
        require(hashlib.sha256((root / 'source' / name).read_bytes()).hexdigest() == expected, 'source_file_hash')
    cases_hash = hashlib.sha256(cases_bytes).hexdigest()
    check(raw, cases, sources, cases_hash)
    candidate = next(i for i,r in enumerate(raw['rows']) if r['variant'] == 'candidate')
    controls = []
    def reject(name, mutate):
        changed = copy.deepcopy(raw)
        mutate(changed)
        require(not same(changed, raw), 'no_op_control')
        try:
            check(changed, cases, sources, cases_hash)
        except (ValueError, KeyError, TypeError) as error:
            controls.append({'name':name, 'reason':str(error)})
        else:
            raise ValueError('accepted_control:' + name)
    reject('missing_row', lambda r:r['rows'].pop())
    reject('duplicate_row', lambda r:r['rows'].__setitem__(-1, copy.deepcopy(r['rows'][0])))
    reject('false_refusal', lambda r:r['rows'][candidate]['response'].__setitem__('dispatched', True))
    reject('consumed_refused_id', lambda r:r['rows'][candidate]['response'].__setitem__('next_id', 2))
    reject('bool_call_count', lambda r:r['rows'][0].__setitem__('initial_call_count', True))
    reject('bool_request_id', lambda r:r['rows'][0]['response'].__setitem__('id', True))
    reject('wrong_forwarded_arguments', lambda r:r['rows'][4]['initial_calls'][0]['arguments']['program']['ops'][0].__setitem__('down', False))
    reject('wrong_source_hash', lambda r:r['sources'].__setitem__('candidate_relay.py', '0'*64))
    reject('wrong_case_hash', lambda r:r.__setitem__('cases_sha256', '0'*64))
    reject('wrong_followup_id', lambda r:r['rows'][candidate]['same_id_followup'].__setitem__('id', 2))
    reject('missing_sdk_timestamp', lambda r:r['rows'][0]['response'].pop('sdk_entry_ns'))
    reject('bool_sdk_timestamp', lambda r:r['rows'][0]['response'].__setitem__('sdk_entry_ns', True))
    report = {'decision':'PASS_ORDINARY_DECODER_REPAIR_SCOPED', 'rows':32,
              'baseline_duplicate_dispatches':8, 'candidate_duplicate_dispatches':0,
              'positive_control_dispatches_per_variant':8, 'effective_controls_rejected':controls,
              'raw_sha256':hashlib.sha256((root / 'raw.json').read_bytes()).hexdigest(),
              'independence':'authored finite oracle; no producer/relay/MCP imports; same author',
              'formal_invocations':0}
    with (root / 'audit.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'decision':report['decision'],'rows':32,'controls_rejected':len(controls)}))


if __name__ == '__main__':
    main()
