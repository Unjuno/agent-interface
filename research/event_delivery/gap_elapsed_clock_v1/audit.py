"""Raw-only independent reconstruction; never imports runner, policy, or model."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import statistics
import sys


def canonical(x: object) -> str:
    return json.dumps(x, sort_keys=True, separators=(',', ':'))

def sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()

def event(seq: int) -> list:
    return [seq, f'E{seq}', sha(f'p{seq}'.encode())]

def prefix(rows: list) -> str:
    return sha(json.dumps(rows, separators=(',', ':')).encode())

def verify_case(folder: Path, spec: dict) -> dict:
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)
    def same(a: object, b: object, message: str) -> None:
        require(canonical(a) == canonical(b), message)
    meta = json.loads((folder/'case.json').read_text())
    same(meta['spec'], spec, 'case specification')
    same(meta['exits'], {'producer': 0, 'consumer': 0}, 'process exits')
    require(meta['error'] is None, 'worker error')
    pids = []
    for role in ('producer', 'consumer'):
        w = meta['workers'][role]
        ready = json.loads(w['ready_line'])
        require(type(w['pid']) is int, 'PID type')
        same(ready, {'ready': True, 'pid': w['pid'], 'role': role}, 'ready binding')
        require((folder/f'{role}.stderr').read_bytes() == b'', 'worker stderr')
        pids.append(w['pid'])
    require(pids[0] != pids[1], 'separate processes')
    expected = {'consumer': [event(3)], 'pending': [],
                'ack': [[2, prefix([event(1), event(2)])]]}
    same(meta['initial'], expected, 'initial database')
    lines = (folder/'journal.jsonl').read_text().splitlines()
    log = [json.loads(x) for x in lines]
    tracker = None
    expected_events = []
    gaps = {}
    accepted = []
    offers = {}
    ack_count = 0
    last_received = 0
    for i, entry in enumerate(log, 1):
        same(entry['before'], expected, f'before state {i}')
        raw_q, raw_r = entry['request_line'], entry['response_line']
        require(raw_q.endswith('\n') and raw_r.endswith('\n'), 'JSONL framing')
        q, r = json.loads(raw_q), json.loads(raw_r)
        same(q['request_id'], f"{spec['id']}:{i}", 'request order/id')
        same(r['request_id'], q['request_id'], 'response id')
        same(r['pid'], meta['workers'][entry['role']]['pid'], 'response PID')
        for key in ('sent_ns', 'received_ns'):
            require(type(entry[key]) is int, 'parent timestamp type')
        for key in ('begin_ns', 'end_ns'):
            require(type(r[key]) is int, 'worker timestamp type')
        require(last_received <= entry['sent_ns'] <= r['begin_ns'] <= r['end_ns'] <= entry['received_ns'], 'same-clock ordering')
        last_received = entry['received_ns']
        op = q['op']
        if entry['scheduled_ms'] is not None:
            ms = entry['scheduled_ms']
            require(type(ms) is int and entry['sent_ns'] >= meta['start_ns'] + ms*1_000_000, 'schedule timing')
            expected_events.append(dict(ms=ms, **{k:v for k,v in q.items() if k!='request_id'}))
        if op == 'offer':
            require(entry['role'] == 'producer', 'producer role')
            seq = q['seq']
            require(type(seq) is int, 'sequence type')
            require(len(expected['pending']) < 2, 'capacity')
            expected['pending'].append([seq]+event(seq))
            expected['pending'].sort(key=lambda row: row[0])
            same(r['status'], 'PENDING_RETAINED', 'offer disposition')
            offers[seq] = r['end_ns']
        elif op == 'ack':
            require(entry['role'] == 'consumer' and spec['scenario'] == 'new_gap', 'explicit ACK scope')
            require(accepted == [4,5] and ack_count == 0, 'ACK after progress only')
            rows = [row for row in expected['consumer'] if row[0] <= 4]
            expected['consumer'] = [row for row in expected['consumer'] if row[0] > 4]
            expected['ack'] = [[4, prefix(rows)]]
            same(r['status'], 'ACK_APPLIED', 'ACK disposition')
            ack_count += 1
        elif op == 'poll':
            require(entry['role'] == 'consumer', 'consumer role')
            steps = r['steps']
            require(type(steps) is list and 1 <= len(steps) <= 3, 'step denominator')
            terminal = False
            for j, step in enumerate(steps):
                require(not terminal, 'step after terminal')
                now = step['observed_ns']
                require(type(now) is int and r['begin_ns'] <= now <= r['end_ns'], 'observation clock')
                if not expected['pending']:
                    want = {'status': 'NO_PENDING', 'observed_ns': now}
                    tracker = None
                    terminal = True
                else:
                    pending = expected['pending'][0]
                    head = pending[1:]
                    mx = max(row[0] for row in expected['consumer'])
                    require(len(expected['consumer']) < 3, 'unexpected full consumer')
                    want = {'head': head, 'observed_ns': now}
                    if head[0] == mx+1:
                        want['status'] = 'EVENT_ACCEPTED'
                        expected['consumer'].append(head)
                        expected['pending'].pop(0)
                        for position, row in enumerate(expected['pending'], 1):
                            row[0] = position
                        accepted.append(head[0])
                        tracker = None
                    else:
                        require(head[0] > mx+1, 'unexpected nonmonotonic case')
                        key = [mx+1, head[0], head[1]]
                        if tracker is None or tracker['key'] != key:
                            tracker = {'key': key, 'first_ns': now, 'count': 0, 'receipt': None}
                        require(now >= tracker['first_ns'], 'clock regression')
                        if tracker['receipt'] is None:
                            tracker['count'] += 1
                            due = (tracker['count'] >= 3 if spec['policy']=='OBS_COUNT_3'
                                   else now >= tracker['first_ns']+80_000_000)
                            if due:
                                material = json.dumps([key, tracker['first_ns']], separators=(',', ':')).encode()
                                tracker['receipt'] = {'type': 'RESYNC_REQUIRED', 'id': sha(material),
                                    'key': key, 'first_ns': tracker['first_ns'], 'authority': False}
                        want.update(status='RESYNC_REQUIRED' if tracker['receipt'] else 'EVENT_PREDECESSOR_MISSING',
                                    state=tracker)
                        g = gaps.setdefault(str(key[0]), {'key': key, 'first_ns': now, 'observations': 0,
                                              'notify_ns': None, 'host_receive_ns': None})
                        g['observations'] += 1
                        if tracker['receipt'] and g['notify_ns'] is None:
                            g['notify_ns'] = now; g['host_receive_ns'] = entry['received_ns']
                        terminal = True
                same(step, want, f'policy or receipt mismatch {i}/{j}')
            require(terminal, 'poll did not terminate')
        elif op == 'stop':
            same(r['status'], 'STOPPED', 'stop response')
        else:
            raise ValueError('unknown operation')
        same(entry['after'], expected, f'after state {i}')
    same(expected_events, spec['events'], 'event schedule cardinality/order')
    first = json.loads(log[0]['request_line'])
    same({k:v for k,v in first.items() if k!='request_id'}, {'op':'offer','seq':5}, 'initial E5')
    same([json.loads(x['request_line'])['op'] for x in log[-2:]], ['stop','stop'], 'terminal stops')
    same([x['role'] for x in log[-2:]], ['producer','consumer'], 'stop role order')
    require(len(log) == len(spec['events']) + 3 + int(spec['scenario']=='new_gap'), 'journal denominator')
    same(meta['final'], expected, 'final snapshot')
    db = folder/'state.sqlite3'
    require(sha(db.read_bytes()) == meta['db_sha256'], 'final database hash')
    with sqlite3.connect(f'file:{db}?mode=ro',uri=True) as con:
        stored={'consumer':[list(x) for x in con.execute('SELECT * FROM consumer ORDER BY seq')],
                'pending':[list(x) for x in con.execute('SELECT * FROM pending ORDER BY pos')],
                'ack':[list(x) for x in con.execute('SELECT * FROM ack')]}
    same(stored, expected, 'independent retained database')
    scenario = spec['scenario']
    if scenario in ('permanent','tail40'):
        same(accepted, [], 'no gap escape')
        require(gaps['4']['notify_ns'] is not None, 'permanent notification liveness')
    else:
        same(accepted, [4,5], 'late predecessor contiguous drain')
        if scenario == 'new_gap':
            require(gaps['6']['notify_ns'] is not None, 'fresh second gap liveness')
        else:
            if spec['policy'] == 'ELAPSED_80MS':
                require(gaps['4']['notify_ns'] is None, 'elapsed policy late-arrival unnecessary notification')
    for gap in gaps.values():
        if gap['notify_ns'] is not None:
            gap['age_ms'] = (gap['notify_ns']-gap['first_ns'])/1e6
            gap['host_age_ms'] = (gap['host_receive_ns']-gap['first_ns'])/1e6
            if spec['policy']=='ELAPSED_80MS':
                require(gap['age_ms'] >= 80, 'notification before elapsed threshold')
    exposure = (scenario not in ('late40','new_gap') or offers[4] < gaps['4']['first_ns']+80_000_000)
    return {'id':spec['id'],'policy':spec['policy'],'profile':spec['profile'],'scenario':scenario,
            'gaps':gaps,'accepted':accepted,'timing_exposure_valid':exposure,'journal_entries':len(log)}


def audit(root: Path, schedule_path: Path, freeze_path: Path | None = None) -> dict:
    errors=[]; rows=[]
    schedule=json.loads(schedule_path.read_text())
    try:
        inv=json.loads((root/'invocation.json').read_text())
        assert canonical(inv['planned']) == canonical(len(schedule['cases'])), 'planned count'
        assert inv['status']=='COMPLETE' and inv['error'] is None, 'incomplete invocation'
        assert canonical(inv['invocations'])=='1' and canonical(inv['reruns'])=='0', 'invocation cardinality'
        assert inv['schedule_sha256']==sha(schedule_path.read_bytes()), 'schedule hash'
        assert [x['id'] for x in inv['completed']]==[x['id'] for x in schedule['cases']], 'case denominator/order'
        assert all(x['status']=='COMPLETE' for x in inv['completed']), 'case completion'
        expected_names={s['id'] for s in schedule['cases']}
        assert {p.name for p in root.iterdir() if p.is_dir()}==expected_names, 'case directories'
        if freeze_path:
            assert inv['freeze_sha256']==sha(freeze_path.read_bytes()), 'freeze hash'
            freeze=json.loads(freeze_path.read_text())
            for name,digest in freeze['sources'].items():
                assert sha((freeze_path.parent/name).read_bytes())==digest, 'source hash: '+name
    except Exception as exc:
        errors.append('allocation: '+str(exc))
    for spec in schedule['cases']:
        try:
            rows.append(verify_case(root/spec['id'],spec))
        except Exception as exc:
            errors.append(spec['id']+': '+str(exc))
    if not errors:
        ages=[r['gaps']['4']['age_ms'] for r in rows if r['scenario']=='permanent' and r['policy']=='OBS_COUNT_3']
        if len({r['profile'] for r in rows})>1 and not (min(ages)<80<=max(ages)):
            errors.append('count-vs-elapsed discriminator unexposed')
    exposures=all(r['timing_exposure_valid'] for r in rows)
    status=('FAIL_LOCAL_AUDIT_OR_GATE' if errors else
            'PASS_LOCAL_CLOCK_BOUNDARY_SCOPED' if exposures else 'HOLD_TIMING_EXPOSURE')
    aggregates=[]
    for policy in ('OBS_COUNT_3','ELAPSED_80MS'):
        for profile in ('fast','slow','paused'):
            selected=[r for r in rows if r['scenario']=='permanent' and r['policy']==policy and r['profile']==profile]
            ages=[r['gaps']['4']['age_ms'] for r in selected if r['gaps']['4']['notify_ns'] is not None]
            if ages:
                aggregates.append({'policy':policy,'profile':profile,'n':len(ages),'min_ms':min(ages),
                    'median_ms':statistics.median(ages),'max_ms':max(ages)})
    return {'status':status,'errors':errors,'planned':len(schedule['cases']),'audited':len(rows),
            'timing_exposure_valid':exposures,'permanent_gap_latency':aggregates,'cases':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,required=True)
    p.add_argument('--schedule',type=Path,required=True); p.add_argument('--freeze',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); result=audit(a.root,a.schedule,a.freeze)
    with a.out.open('x') as handle:
        handle.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
    sys.exit(0 if result['status']=='PASS_LOCAL_CLOCK_BOUNDARY_SCOPED' else 2)
