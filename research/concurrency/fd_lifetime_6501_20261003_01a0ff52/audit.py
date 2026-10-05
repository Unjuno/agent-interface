"""Independent saved-event ledger/oracle; imports no candidate or ownership code."""
import datetime
import errno
import hashlib
import itertools
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
INPUT = json.loads((ROOT / 'input.json').read_bytes())
CLOSED = {'state': 'closed', 'errno': errno.EBADF}
FIELDS = {
    'row_open': {'original_fd','original_write_fd','sentinel_fd','sentinel_write_fd','original_identity','sentinel_identity'},
    'worker_enter': {'fd'}, 'read_return': {'fd','hex'}, 'worker_exit': set(),
    'close_claim': {'claimed','fd'}, 'close_requested': {'fd','identity'}, 'close_return': {'fd','status','errno'},
    'blocked_observed': {'label','observation'}, 'caller_close_checkpoint': {'slot_identity','worker_done'},
    'dup2_requested': {'source_fd','target_fd','source_identity'},
    'dup2_return': {'source_fd','target_fd','returned_fd','replacement_identity'},
    'alias_closed': {'fd'}, 'write_requested': {'fd','hex','purpose'}, 'write_return': {'fd','count','purpose'},
    'thread_joined': {'tid','proc_absent'}, 'reused_slot_checkpoint': {'slot_identity','worker_done'},
    'primary_checkpoint': {'state'}, 'harness_closed': {'fd','identity'},
    'final_checkpoint': {'fds','thread_alive','proc_absent'},
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def exact(actual, expected, path='value'):
    need(type(actual) is type(expected), path + ': type')
    if type(expected) is dict:
        need(set(actual) == set(expected), path + ': keys')
        for key, value in expected.items():
            exact(actual[key], value, path + '.' + key)
    elif type(expected) is list:
        need(len(actual) == len(expected), path + ': length')
        for index, value in enumerate(expected):
            exact(actual[index], value, path + '[' + str(index) + ']')
    else:
        need(actual == expected, path + ': value')


def open_identity(value):
    need(type(value) is dict and set(value) == {'state','device','inode','kind'}, 'open identity schema')
    need(value['state'] == 'open' and all(type(value[k]) is int for k in ('device','inode','kind')), 'identity types')
    need(value['device'] >= 0 and value['inode'] > 0 and value['kind'] == 4096, 'actual FIFO identity')


def row_audit(row):
    need(set(row) == {'kind','policy','schedule','failure','worker_failure','worker_cleanup_failure','events','primary','final'}, 'row schema')
    need(all(row[k] is None for k in ('failure','worker_failure','worker_cleanup_failure')), 'first construction failures')
    policy, schedule = row['policy'], row['schedule']
    need(type(row['events']) is list and 10 < len(row['events']) < 80, 'bounded events')
    events = row['events']
    need(events[0]['kind'] == 'row_open' and events[-1]['kind'] == 'final_checkpoint', 'row boundaries')
    opened = events[0]
    r, w, sr, sw = [opened[k] for k in ('original_fd','original_write_fd','sentinel_fd','sentinel_write_fd')]
    need(all(type(fd) is int and fd >= 3 for fd in (r,w,sr,sw)) and len({r,w,sr,sw}) == 4, 'owned unique FD slots')
    original, sentinel = opened['original_identity'], opened['sentinel_identity']
    open_identity(original)
    open_identity(sentinel)
    need(original != sentinel, 'distinct original/replacement pipe identities')
    enter = [e for e in events if e['kind'] == 'worker_enter']
    need(len(enter) == 1, 'one native worker')
    caller_tid, worker_tid = opened['native_tid'], enter[0]['native_tid']
    need(type(caller_tid) is int and type(worker_tid) is int and caller_tid > 0 and worker_tid > 0 and caller_tid != worker_tid, 'native role identity')
    ledger = {r: original, w: original, sr: sentinel, sw: sentinel}
    close_claims, requested, writes = {}, {}, {}
    counts = {kind: 0 for kind in FIELDS}
    seen_blocks = []
    close_identities = []
    positions = {}
    once_claims = 0
    has_returned = False
    has_exited = False
    has_joined = False
    has_primary = False
    has_reused = False
    duplicate_pending = False
    for index, event in enumerate(events):
        kind = event['kind']
        need(kind in FIELDS and set(event) == {'seq','kind','actor','native_tid'} | FIELDS[kind], 'event schema ' + kind)
        exact(event['seq'], index, 'sequence')
        actor = event['actor']
        need(actor in ('caller','worker'), 'actor vocabulary')
        exact(event['native_tid'], worker_tid if actor == 'worker' else caller_tid, 'event native actor')
        if kind in ('worker_enter','read_return','worker_exit'):
            need(actor == 'worker', 'worker event role')
        elif kind not in ('close_claim','close_requested','close_return'):
            need(actor == 'caller', 'harness/observer role')
        counts[kind] += 1
        positions.setdefault(kind, []).append(index)
        if kind == 'worker_enter':
            exact(event['fd'], r)
        elif kind == 'blocked_observed':
            need(not has_returned, 'blocked witness before read completion')
            exact(event['observation'], {'tid': worker_tid, 'state':'S','wchan':'anon_pipe_read','syscall_nr':63,'fd':r}, 'kernel witness')
            seen_blocks.append(event['label'])
            if event['label'] == 'before_action':
                exact(ledger[r], original, 'initial read description')
            elif event['label'] == 'after_caller_close':
                exact(ledger[r], CLOSED, 'closed read slot while kernel read remains blocked')
            elif event['label'] == 'after_reuse':
                exact(ledger[r], sentinel, 'reused slot differs from blocked original read')
                need(has_reused, 'after-reuse witness')
            else:
                raise ValueError('unknown blocked label')
        elif kind == 'close_claim':
            need(actor not in close_claims, 'one cleanup per actor')
            claimed = policy == 'integer_copies' or once_claims == 0
            exact(event['claimed'], claimed, 'one-time claim')
            exact(event['fd'], r if claimed else None, 'claimed original FD slot')
            close_claims[actor] = claimed
            if claimed:
                once_claims += 1
        elif kind == 'close_requested':
            need(close_claims.get(actor) is True and actor not in requested, 'actual owned close request')
            exact(event['fd'], r)
            exact(event['identity'], ledger[r], 'actual close target identity')
            need(ledger[r]['state'] == 'open', 'close targets current live object')
            requested[actor] = ledger[r]
        elif kind == 'close_return':
            need(actor in requested, 'close return request')
            exact(event['fd'], r)
            exact(event['status'], 'closed')
            exact(event['errno'], None)
            close_identities.append({'actor': actor, 'identity': requested[actor]})
            ledger[r] = CLOSED
        elif kind == 'caller_close_checkpoint':
            exact(event['slot_identity'], CLOSED)
            exact(event['worker_done'], False)
            need(schedule == 'caller_close_reuse_before_worker_finally', 'caller close checkpoint schedule')
        elif kind == 'dup2_requested':
            need(not has_reused and not duplicate_pending, 'single fresh reuse')
            exact(ledger[r], CLOSED, 'reuse only vacated slot')
            exact(ledger[sr], sentinel, 'owned replacement source open')
            exact({key:event[key] for key in ('source_fd','target_fd','source_identity')}, {'source_fd':sr,'target_fd':r,'source_identity':sentinel})
            duplicate_pending = True
        elif kind == 'dup2_return':
            need(duplicate_pending, 'reuse requested before return')
            exact({key:event[key] for key in ('source_fd','target_fd','returned_fd','replacement_identity')}, {'source_fd':sr,'target_fd':r,'returned_fd':r,'replacement_identity':sentinel})
            ledger[r] = sentinel
            has_reused = True
            duplicate_pending = False
        elif kind == 'alias_closed':
            need(has_reused, 'alias only after replacement exists')
            exact(event['fd'], sr)
            ledger[sr] = CLOSED
        elif kind == 'write_requested':
            purpose = event['purpose']
            need(purpose not in writes and not has_primary, 'one ordered write purpose')
            expected_fd = sw if purpose in ('replacement_data','positive_sentinel_data') else w
            expected_hex = INPUT['replacement_hex'] if expected_fd == sw else INPUT['data_hex']
            exact(event['fd'], expected_fd)
            exact(event['hex'], expected_hex)
            need(ledger[expected_fd]['state'] == 'open', 'write FD owned/open')
            writes[purpose] = {'requested':index,'returned':None}
        elif kind == 'write_return':
            need(event['purpose'] in writes and writes[event['purpose']]['returned'] is None, 'one write return')
            exact(event['fd'], sw if event['purpose'] in ('replacement_data','positive_sentinel_data') else w)
            exact(event['count'], 1)
            writes[event['purpose']]['returned'] = index
        elif kind == 'read_return':
            need(not has_returned, 'one old read result')
            purpose = 'harness_release_old_read' if schedule == 'caller_close_reuse_before_worker_finally' else 'primary_data'
            need(purpose in writes, 'original data write precedes read result')
            exact(event['fd'], r)
            exact(event['hex'], INPUT['data_hex'], 'original description returns original D, never replacement R')
            has_returned = True
        elif kind == 'worker_exit':
            need(has_returned and 'worker' in close_claims, 'worker cleanup after read')
            need(not close_claims['worker'] or 'worker' in requested, 'worker close completed')
            has_exited = True
        elif kind == 'thread_joined':
            need(has_exited, 'worker exit before native join')
            exact(event['tid'], worker_tid)
            exact(event['proc_absent'], True)
            has_joined = True
        elif kind == 'reused_slot_checkpoint':
            exact(event['slot_identity'], sentinel)
            exact(event['worker_done'], False)
            need(has_reused and not has_returned, 'replacement ready while old read blocked')
        elif kind == 'primary_checkpoint':
            need(has_joined and not has_primary, 'one primary checkpoint after native join')
            destroyed = policy == 'integer_copies' and schedule != 'normal_finish'
            probe_fd = sr if schedule == 'normal_finish' else r
            expected_probe = {'state':'closed','hex':None,'errno':9} if destroyed else {'state':'open','hex':INPUT['replacement_hex'],'errno':None}
            expected = {'probe_fd':probe_fd,'identity':CLOSED if destroyed else sentinel,'probe':expected_probe,'worker_hex':INPUT['data_hex'],'worker_done':True,'thread_alive':False}
            exact(event['state'], expected, 'independent primary result')
            exact(row['primary'], expected, 'primary aggregate matches actual event')
            exact(ledger[probe_fd], expected['identity'], 'probe ledger identity')
            has_primary = True
        elif kind == 'harness_closed':
            need(has_primary, 'common cleanup only after scoring')
            fd = event['fd']
            need(type(fd) is int and fd in ledger and ledger[fd]['state'] == 'open', 'cleanup current owned resource')
            exact(event['identity'], ledger[fd], 'cleanup identity')
            ledger[fd] = CLOSED
        elif kind == 'final_checkpoint':
            expected_fds = {str(fd): CLOSED for fd in sorted(ledger)}
            need(has_primary and all(value == CLOSED for value in ledger.values()), 'final closed ledger')
            exact(event['fds'], expected_fds)
            exact(row['final'], expected_fds)
            exact(event['thread_alive'], False)
            exact(event['proc_absent'], True)
    expected_closers = {'worker'} if schedule == 'normal_finish' else {'worker','caller'}
    need(set(close_claims) == expected_closers and not duplicate_pending, 'complete cleanup actors/reuse')
    cancels_first = schedule == 'caller_close_reuse_before_worker_finally'
    hazard = schedule != 'normal_finish'
    destroyed = policy == 'integer_copies' and hazard
    expected_counts = {'row_open':1,'worker_enter':1,'read_return':1,'worker_exit':1,
                       'close_claim':len(expected_closers),'close_requested':2 if destroyed else 1,'close_return':2 if destroyed else 1,
                       'blocked_observed':3 if cancels_first else 1,'caller_close_checkpoint':int(cancels_first),
                       'dup2_requested':int(hazard),'dup2_return':int(hazard),'alias_closed':int(hazard),
                       'write_requested':2,'write_return':2,'thread_joined':1,'reused_slot_checkpoint':int(cancels_first),
                       'primary_checkpoint':1,'harness_closed':2 if destroyed else 3,'final_checkpoint':1}
    exact(counts, expected_counts, 'complete event roster')
    need(all(value['returned'] is not None for value in writes.values()), 'complete write receipts')
    if schedule == 'caller_close_reuse_before_worker_finally':
        exact(seen_blocks, ['before_action','after_caller_close','after_reuse'])
        need(positions['reused_slot_checkpoint'][0] < writes['harness_release_old_read']['requested'], 'reuse before original release')
        expected_purposes = {'replacement_data','harness_release_old_read'}
        expected_first = 'caller'
    else:
        exact(seen_blocks, ['before_action'])
        expected_purposes = {'primary_data','positive_sentinel_data'} if schedule == 'normal_finish' else {'primary_data','replacement_data'}
        expected_first = 'worker'
        if schedule != 'normal_finish':
            need(positions['thread_joined'][0] < positions['dup2_requested'][0] < next(e['seq'] for e in events if e['kind']=='close_claim' and e['actor']=='caller'), 'native worker finished then reused then late caller')
    need(set(writes) == expected_purposes, 'frozen write/cleanup distinction')
    need(close_identities[0] == {'actor':expected_first,'identity':original}, 'first closer original object')
    if policy == 'integer_copies' and schedule != 'normal_finish':
        need(len(close_identities) == 2 and close_identities[1]['identity'] == sentinel, 'late cleanup destroys replacement object')
    else:
        need(len(close_identities) == 1, 'one-time original closure only')
    return {'policy':policy,'schedule':schedule,'replacement_closed_by_stale_cleanup':policy=='integer_copies' and schedule!='normal_finish','original_read_completed':True,'native_thread_gone':True}


def audit_records(records):
    need(type(records) is list and len(records) == 8, 'header/six rows/footer coverage')
    header, footer = records[0], records[-1]
    need(set(header) == {'kind','allocation','started_utc','input_sha256','environment'}, 'header schema')
    need(set(footer) == {'kind','allocation','ended_utc','rows'}, 'footer schema')
    exact(header['kind'], 'header')
    exact(footer['kind'], 'footer')
    exact(header['allocation'], INPUT['allocation'])
    exact(footer['allocation'], INPUT['allocation'])
    exact(footer['rows'], 6)
    exact(header['input_sha256'], hashlib.sha256((ROOT/'input.json').read_bytes()).hexdigest())
    expected_environment = json.loads((ROOT/'environment.json').read_bytes())
    exact(header['environment'], expected_environment, 'actual frozen image/backend/cgroup pins')
    start, end = datetime.datetime.fromisoformat(header['started_utc']), datetime.datetime.fromisoformat(footer['ended_utc'])
    need(start.tzinfo is not None and end.tzinfo is not None and start < end, 'actual UTC start/end')
    rows = records[1:-1]
    exact([[r['policy'],r['schedule']] for r in rows], [list(pair) for pair in itertools.product(INPUT['policies'],INPUT['schedules'])], 'fixed row domain/order')
    reductions = [row_audit(row) for row in rows]
    need(sum(r['replacement_closed_by_stale_cleanup'] for r in reductions) == 2, 'two integer-only cross-lifetime closures')
    return {'status':'PASS_FD_LIFETIME_BOUNDARY_SCOPED','rows':6,'events':sum(len(r['events']) for r in rows),'integer_replacement_failures':2,'once_owner_replacement_failures':0,'normal_positives':2,'errors':[],'reductions':reductions}


def parse_line(data):
    def members(pairs):
        result = {}
        for key,value in pairs:
            need(key not in result, 'duplicate JSON member')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON constant ' + value)
    return json.loads(data, object_pairs_hook=members, parse_constant=constant)


def main():
    raw_path, output = map(pathlib.Path, sys.argv[1:3])
    raw = raw_path.read_bytes()
    try:
        need(0 < len(raw) <= INPUT['raw_byte_cap'] and raw.endswith(b'\n'), 'bounded complete raw')
        result = audit_records([parse_line(line) for line in raw.splitlines()])
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        result = {'status':'FAIL_FD_LIFETIME_EVIDENCE','errors':[str(exc)]}
    result.update({'raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_bytes':len(raw),'auditor_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()})
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return 0 if result['status']=='PASS_FD_LIFETIME_BOUNDARY_SCOPED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
