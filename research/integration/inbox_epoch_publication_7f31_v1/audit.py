"""Raw-only independent audit; never imports runner or candidate/upstream code."""
import base64
from collections import Counter
import copy
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sys

POLICIES = ('CALLER_ID_ONLY', 'SIDECAR_PRECHECK', 'PIN_ONCE')
SCHEDULES = ('STABLE_A', 'SWITCH_BEFORE_PREPARE', 'SWITCH_BETWEEN_CHECK_AND_READ',
             'SWITCH_AFTER_READ_BEFORE_RETURN', 'FRESH_B_CURSOR')
BLOBS = {'research/integration/event_inbox_reader_v1/reader.py': 'ea72c166c2cea511ea91031dfbb14563fe4e3245',
         'research/live_control/delivery_ledger_v2.py': 'fb50be9d4d821a7836e6a0158c53a983f0f91df5'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, label):
    if not condition:
        raise ValueError(label)


def unique(pairs):
    output = {}
    for key, value in pairs:
        need(key not in output, 'duplicate_json_key')
        output[key] = value
    return output


def parse(value):
    return json.loads(value, object_pairs_hook=unique,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite_json')))


def check_receipt(receipt, records, encoded, epoch, tail):
    need(set(receipt) == {'schema','records','tail_state','problem','next_cursor',
                         'authority','acknowledged','input_dispatched'}, 'receipt_fields')
    need(receipt['schema'] == 'agent-interface/experimental-inbox-read-v1', 'receipt_schema')
    need(receipt['records'] == records and receipt['tail_state'] == tail and
         receipt['problem'] is None, 'receipt_content')
    need(receipt['authority'] == 'none' and receipt['acknowledged'] is False and
         receipt['input_dispatched'] is False, 'authority_changed')
    cursor = receipt['next_cursor']
    need(type(cursor['offset']) is int and type(cursor['next_sequence']) is int, 'cursor_integer')
    need(cursor == {'schema': 'agent-interface/experimental-read-cursor-v1', 'stream_id': epoch,
        'offset': len(encoded), 'prefix_sha256': digest(encoded),
        'next_sequence': encoded.count(b'\n') + 1}, 'cursor_binding')


def audit(raw, freeze=None, construction=False):
    need(raw['schema'] == 'issue3938-raw-v1' and raw['construction'] is construction, 'allocation_kind')
    need('stop' not in raw, 'runner_stop')
    reps = 1 if construction else 3
    wanted = set(itertools.product(POLICIES, SCHEDULES, range(1, reps+1)))
    need(len(raw['cases']) == len(wanted), 'case_count')
    need(set(raw['sources']) == set(BLOBS), 'upstream_set')
    for path, blob in BLOBS.items():
        need(raw['sources'][path]['git_blob'] == blob, 'source_blob')
    if not construction:
        need(freeze is not None and raw['freeze'] == freeze, 'freeze_binding')
        for path in BLOBS:
            need(raw['sources'][path]['sha256'] == freeze['sha256'][path], 'source_digest')
    seen = set()
    summary = {p: Counter(cases=0, accepted=0, refused=0, cross_generation=0) for p in POLICIES}
    cells = []
    for row in raw['cases']:
        p, s, rep = row['policy'], row['schedule'], row['repetition']
        need(type(rep) is int, 'repetition_integer')
        key = (p, s, rep)
        need(key in wanted and key not in seen, 'case_identity')
        seen.add(key)
        need(row['id'] == f'{p}-{s}-{rep}' and 'error' not in row, 'case_label')
        need(row['before'] == row['after'], 'generation_mutation')
        need(set(row['before']) == {g+'/'+n for g in ('A','B') for n in ('epoch.json','delivered.jsonl')}, 'generation_files')
        data, records = {}, {}
        for gen in ('A', 'B'):
            for name in ('epoch.json', 'delivered.jsonl'):
                meta = row['before'][gen + '/' + name]
                b = meta['text'].encode()
                need(meta['sha256'] == digest(b) and type(meta['size']) is int and meta['size'] == len(b), 'file_digest')
                need(type(meta['inode']) is int and type(meta['device']) is int, 'file_identity_type')
            need(parse(row['before'][gen+'/epoch.json']['text']) == {'epoch': gen}, 'epoch_metadata')
            data[gen] = row['before'][gen+'/delivered.jsonl']['text'].encode()
            records[gen] = [parse(line) for line in data[gen].splitlines()]
            wanted_records = [{'delivery_id': f'delivery:{i}', 'event': 'notification',
                               'payload': {'value': value}} for i, value in enumerate(
                                   ('common-1', 'common-2', gen+'-tail'), 1)]
            need(records[gen] == wanted_records, 'fixture_records')
        need(data['A'].splitlines(keepends=True)[:2] == data['B'].splitlines(keepends=True)[:2], 'shared_prefix')
        first = data['A'].splitlines(keepends=True)[0]
        check_receipt(row['initial'], [records['A'][0]], first, 'A', 'limit')
        epoch = 'B' if s == 'FRESH_B_CURSOR' else 'A'
        need(row['request'] == {'policy': p, 'stream_id': epoch,
             'cursor': None if epoch == 'B' else row['initial']['next_cursor']}, 'request_binding')
        expected = [('reader','ready'),('publisher','ready')]
        if s in ('SWITCH_BEFORE_PREPARE','FRESH_B_CURSOR'):
            expected += [('publisher','publish')]
        expected += [('reader','prepare')]
        if s == 'SWITCH_BETWEEN_CHECK_AND_READ':
            expected += [('publisher','publish')]
        expected += [('reader','read')]
        if s == 'SWITCH_AFTER_READ_BEFORE_RETURN':
            expected += [('publisher','publish')]
        expected += [('reader','return'),('reader','quit'),('publisher','quit')]
        need([(e['actor'], e['command']) for e in row['events']] == expected, 'barrier_order')
        need(set(row['exits']) == {'reader','publisher'}, 'missing_exit')
        need(set(row['processes']) == {'reader','publisher'}, 'process_set')
        need(row['processes']['reader']['pid'] != row['processes']['publisher']['pid'], 'distinct_processes')
        for role in ('reader','publisher'):
            need(row['exits'][role] == {'code':0, 'stderr':'', 'trailing_stdout':''} and
                 type(row['exits'][role]['code']) is int, 'process_exit')
            proc = row['processes'][role]
            need(type(proc['pid']) is int and proc['pid'] > 0, 'process_pid')
            cmd = proc['command']
            need(cmd[1:3] == ['-S','-B'] and Path(cmd[3]).name == 'run.py' and
                 cmd[4:6] == ['worker',role] and Path(cmd[6]).name == row['id'], 'process_command')
        refused = p != 'CALLER_ID_ONLY' and s == 'SWITCH_BEFORE_PREPARE'
        selected_gen = 'B' if s in ('SWITCH_BEFORE_PREPARE','FRESH_B_CURSOR') else 'A'
        current, previous_ns, returned = 'epochs/A', -1, None
        for e in row['events']:
            need(type(e['observed_ns']) is int and e['observed_ns'] > previous_ns, 'event_clock')
            previous_ns = e['observed_ns']
            message = parse(e['stdout'])
            c, role = e['command'], e['actor']
            if c == 'ready':
                need(message == {'ready':role, 'pid':row['processes'][role]['pid'], 'sources':raw['sources']}, 'worker_identity')
            elif c == 'publish':
                need(message == {'done':'publish','before':'epochs/A','after':'epochs/B'}, 'publication_receipt')
                current = 'epochs/B'
            elif c == 'prepare':
                need(message == {'done':'prepare', 'selected':'epochs/'+selected_gen if p == 'PIN_ONCE' else 'CURRENT',
                    'observed_epoch':None if p == 'CALLER_ID_ONLY' else selected_gen,
                    'problem':'EPOCH_MISMATCH' if refused else None}, 'preparation_binding')
            elif c == 'read':
                need(message == {'done':'read','problem':'EPOCH_MISMATCH' if refused else None}, 'read_boundary')
            elif c == 'return':
                returned = message
            elif c == 'quit':
                need(message == {'done':'quit'}, 'quit_receipt')
            need(e['current'] == current, 'observed_pointer')
        need(row['final_current'] == current, 'final_pointer')
        counts = summary[p]
        counts['cases'] += 1
        if refused:
            need(returned == {'done':'return','problem':'EPOCH_MISMATCH','receipt':None}, 'refusal_exposure')
            counts['refused'] += 1
            outcome = 'REFUSED'
        else:
            gen = 'B' if s in ('SWITCH_BEFORE_PREPARE','SWITCH_BETWEEN_CHECK_AND_READ','FRESH_B_CURSOR') else 'A'
            if p == 'PIN_ONCE' and s == 'SWITCH_BETWEEN_CHECK_AND_READ':
                gen = 'A'
            need(set(returned) == {'done','problem','receipt'} and returned['done'] == 'return' and
                 returned['problem'] is None, 'return_boundary')
            check_receipt(returned['receipt'], records[gen] if epoch == 'B' else records[gen][1:], data[gen], epoch, 'end')
            counts['accepted'] += 1
            counts['cross_generation'] += int(gen != epoch)
            outcome = 'CROSS_GENERATION' if gen != epoch else 'CONSISTENT_' + gen
        cells.append({'policy':p, 'schedule':s, 'repetition':rep, 'outcome':outcome})
    need(seen == wanted, 'coverage')
    return {'decision':'PASS_GENERATION_LOOKUP_BOUNDARY_SCOPED', 'cases':len(seen),
            'construction':construction, 'summary':summary, 'cells':cells,
            'scope':'trusted retained immutable generations; not current-action authority or production'}


def controls(raw, freeze, construction):
    controls_out = []
    mutations = []
    mutations.append(('missing_case', lambda x: x['cases'].pop()))
    mutations.append(('duplicate_case', lambda x: x['cases'].__setitem__(-1, copy.deepcopy(x['cases'][0]))))
    mutations.append(('boolean_repetition', lambda x: x['cases'][0].__setitem__('repetition', True)))
    mutations.append(('missing_publisher_exit', lambda x: x['cases'][0]['exits'].pop('publisher')))
    mutations.append(('changed_prefix_bytes', lambda x: x['cases'][0]['after']['A/delivered.jsonl'].__setitem__('text','wrong\n')))
    mutations.append(('changed_source_blob', lambda x: x['sources'][next(iter(BLOBS))].__setitem__('git_blob','0'*40)))
    mutations.append(('wrong_pointer', lambda x: x['cases'][0]['events'][0].__setitem__('current','epochs/B')))
    def returned_mutation(x, field, value):
        for event in x['cases'][0]['events']:
            if event['command'] == 'return':
                message = parse(event['stdout'])
                if field == 'prefix':
                    message['receipt']['next_cursor']['prefix_sha256'] = value
                else:
                    message['receipt'][field] = value
                event['stdout'] = json.dumps(message) + '\n'
    mutations.append(('cursor_hash', lambda x: returned_mutation(x, 'prefix', '0'*64)))
    mutations.append(('authority_flag', lambda x: returned_mutation(x, 'input_dispatched', True)))
    for label, mutate in mutations:
        candidate = copy.deepcopy(raw)
        mutate(candidate)
        try:
            audit(candidate, freeze, construction)
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            controls_out.append({'control':label,'rejected':True,'reason':str(exc)})
        else:
            controls_out.append({'control':label,'rejected':False})
    need(all(x['rejected'] for x in controls_out), 'corruption_control_accepted')
    return controls_out


if __name__ == '__main__':
    construction = '--construction' in sys.argv
    path = Path(sys.argv[1])
    data = path.read_bytes()
    if path.name.endswith('.b64'):
        data = gzip.decompress(base64.b64decode(data, validate=False))
    raw = parse(data)
    freeze = None if construction else parse((Path(__file__).parent / 'FREEZE.json').read_bytes())
    try:
        report = audit(raw, freeze, construction)
        report['corruption_controls'] = controls(raw, freeze, construction)
        report['raw_sha256'] = digest(data)
        report['errors'] = []
        print(json.dumps(report, sort_keys=True, indent=2))
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        print(json.dumps({'decision':'HOLD_AUDIT','error':str(exc),'raw_sha256':digest(data)}))
        raise SystemExit(2)
