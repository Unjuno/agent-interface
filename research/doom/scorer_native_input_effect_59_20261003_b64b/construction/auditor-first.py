"""Data-only native trace oracle; imports no producer or retained runtime."""
import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path


def canonical(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def verify(raw, deck, root):
    errors = []

    def need(ok, label):
        if not ok:
            errors.append(label)

    need(raw.get('schema') == 'native-scorer-input-59-v1', 'SCHEMA')
    rows = raw.get('rows', [])
    need([r.get('case', {}).get('id') for r in rows] == [c['id'] for c in deck], 'ROSTER')
    for row, case in zip(rows, deck):
        label = case['id'] + ':'
        need(canonical(row.get('case')) == canonical(case), label+'CASE')
        ints = [row.get(k) for k in ('owner_thread', 'pipe_inode', 'start_ns', 'end_ns', 'period_ns')]
        ints.append(row.get('runtime', {}).get('pid'))
        if not all(type(v) is int and v > 0 for v in ints):
            errors.append(label+'INT_TYPE')
            continue
        need(row['period_ns'] == 2_000_000, label+'PERIOD')
        need(row['end_ns'] >= row['start_ns'], label+'WALL_ORDER')
        need(row.get('pipe_is_fifo') is True, label+'PIPE')
        need(row.get('read_fd_closed') is True, label+'CLOSED')
        need(row['runtime'].get('machine') == 'aarch64', label+'RUNTIME')
        need(row['runtime'].get('perf_counter', {}).get('monotonic') is True, label+'MONOTONIC')
        for name, value in [('cpu.max', '100000 100000'), ('memory.max', '268435456'), ('pids.max', '64')]:
            need(row['runtime'].get(name) == value, label+'CGROUP_'+name)
        receipt = row.get('process_receipt', {})
        need(type(receipt.get('exit_code')) is int and receipt['exit_code'] == 0, label+'PROCESS_EXIT')
        try:
            need(datetime.fromisoformat(receipt['utc_start']) <= datetime.fromisoformat(row['utc_start'])
                 <= datetime.fromisoformat(row['utc_end']) <= datetime.fromisoformat(receipt['utc_end']), label+'UTC_JOIN')
        except (KeyError, ValueError, TypeError):
            errors.append(label+'UTC_JOIN')
        artifacts = row.get('artifacts', {})
        for rel, pin in artifacts.items():
            path = Path(rel)
            if path.is_absolute() or '..' in path.parts or not rel.startswith(case['id']+'/'):
                errors.append(label+'ARTIFACT_PATH')
                continue
            f = root / rel
            need(f.is_file(), label+'ARTIFACT_MISSING')
            if f.is_file():
                b = f.read_bytes()
                need(type(pin.get('bytes')) is int and len(b) == pin['bytes']
                     and hashlib.sha256(b).hexdigest() == pin.get('sha256'), label+'ARTIFACT_HASH')
        cell = root / case['id']
        actual_paths = {str(f.relative_to(root)) for f in cell.rglob('*') if f.is_file()}
        need(set(artifacts) == actual_paths, label+'ARTIFACT_ROSTER')
        saved = cell / 'row.json'
        if saved.exists():
            stripped = {k: v for k, v in row.items() if k not in ('artifacts', 'process_receipt')}
            need(canonical(json.loads(saved.read_text())) == canonical(stripped), label+'ROW_JOIN')

        ev = row.get('events', [])
        if not all(type(e.get('ns')) is int and type(e.get('thread_id')) is int for e in ev):
            errors.append(label+'EVENT_INT_TYPE')
            continue
        need(all(a['ns'] <= b['ns'] for a,b in zip(ev,ev[1:])), label+'EVENT_ORDER')
        need(all(e['thread_id'] == row['owner_thread'] for e in ev), label+'OWNER_THREAD')
        queues = [e for e in ev if e['kind'] == 'prequeued']
        need(len(queues) == 1 and queues[0].get('hex') == case['input_hex']
             and queues[0].get('writer_closed') is True and queues[0].get('written') == 10, label+'PREQUEUED')
        reads = [e for e in ev if e['kind'] == 'read']
        chunks = [bytes.fromhex(e['hex']) for e in reads]
        need(all(len(b) <= case['read_limit'] for b in chunks), label+'READ_LIMIT')
        wire = b''.join(chunks)
        expected = bytes.fromhex(case['input_hex'])
        need(expected.startswith(wire), label+'WIRE')
        needed_lines = ['α','FINISH'] if row.get('disposition') == 'finish' else []
        need(row.get('commands') == needed_lines, label+'COMMANDS')
        need([e.get('line') for e in ev if e['kind']=='command'] == needed_lines, label+'COMMAND_TRACE')
        if needed_lines:
            need(wire == expected, label+'COMPLETE_WIRE')
            effect_path = cell/'effect.json'
            need(effect_path.is_file(), label+'EFFECT_MISSING')
            if effect_path.exists():
                expected_effect = {'schema':'disposable-finish-effect-v1','cell_id':case['id'],
                                   'commands':['α','FINISH'],'finished':True}
                need(canonical(json.loads(effect_path.read_text())) == canonical(expected_effect), label+'EFFECT')
            need(sum(e['kind']=='effect_saved' for e in ev)==1, label+'EFFECT_TRACE')
        else:
            need(not (cell/'effect.json').exists(), label+'NO_EFFECT')

        sampled = [e for e in ev if e['kind']=='sample_end']
        begins = [e for e in ev if e['kind']=='sample_begin']
        need(len(sampled)==len(begins)==len(row.get('samples',[])), label+'SAMPLE_COUNT')
        for i,(begin,end) in enumerate(zip(begins,sampled)):
            need(begin.get('index')==end.get('index')==i, label+'SAMPLE_INDEX')
            need(end['ns']-begin['ns']>=case['sleep_ns'], label+'COST_FLOOR')
            need(row['samples'][i] == {'index':i,'payload_ns':end.get('payload_ns')}, label+'PAYLOAD_JOIN')
        file = cell/'scorer/scorer-samples.jsonl'
        scorer = [json.loads(s) for s in file.read_text().splitlines()] if file.exists() else []
        sink_begin = [e for e in ev if e['kind']=='sink_begin']
        sink_end = [e for e in ev if e['kind']=='sink_end']
        need(len(scorer)==len(sampled)==len(sink_begin)==len(sink_end), label+'SCORER_COUNT')
        need(not (cell/'scorer/scorer-events.jsonl').exists(), label+'ZERO_EVENTS')
        clocks = []
        decisions = []
        for e in ev:
            if e['kind']=='clock':
                clocks.append(e['ns'])
            elif e['kind']=='sample_begin':
                need(len(clocks)>=2, label+'CLOCK_JOIN')
                if len(clocks)>=2:
                    decisions.append((clocks[-2],clocks[-1]))
        if not clocks:
            errors.append(label+'NO_CLOCK')
            continue
        schedule = clocks[0]
        total_missed = 0
        for i,(s,begin,end,decision) in enumerate(zip(scorer,sink_begin,sink_end,decisions)):
            if not all(type(s.get(k)) is int for k in ('scheduled_ns','sample_started_ns','sample_finished_ns','start_lateness_ns','missed_periods_before')):
                errors.append(label+'RECEIPT_INT_TYPE')
                continue
            now, sample_start = decision
            missed = max(0,(now-schedule)//row['period_ns'])
            need(s['scheduled_ns']==schedule and s['missed_periods_before']==missed,
                 label+'SCHEDULE')
            need(s['sample_started_ns']==sample_start and s['sample_finished_ns'] in clocks
                 and s['sample_started_ns']<=s['payload']['sample_ns']<=s['sample_finished_ns'], label+'RECEIPT_CLOCK')
            need(s['start_lateness_ns']==max(0,sample_start-schedule), label+'LATENESS')
            expected_payload={'schema':'independent-progress-sample-v2','sample_ns':sampled[i]['payload_ns'],
                 'kill_count':0,'death_count':0,'episode_finished':False,'player_dead':False,'map_exit':False}
            need(canonical(s['payload'])==canonical(expected_payload) and s.get('controller_visible') is False, label+'SCORER_PRIVATE')
            need(canonical(begin.get('receipt'))==canonical({k:v for k,v in s.items() if k not in ('payload','controller_visible')}), label+'SINK_JOIN')
            need(end.get('count')==i+1 and begin['ns']<=end['ns'], label+'SINK_ORDER')
            schedule += (missed+1)*row['period_ns']
            total_missed += missed
        stats=row.get('stats')
        if stats is not None:
            need(stats.get('samples')==len(sampled) and stats.get('commands')==len(needed_lines)
                 and stats.get('missed_sample_periods')==total_missed and stats.get('owner_thread_id')==row['owner_thread'], label+'STATS')
        if row.get('disposition')=='sample_budget':
            need(len(sampled)==case['sample_budget'] and len([e for e in ev if e['kind']=='sample_budget'])==1, label+'BUDGET')
        else:
            need(row.get('disposition')=='finish' and len(sampled)<=case['sample_budget'], label+'DISPOSITION')
    return sorted(set(errors))


def controls(raw, deck, root):
    mutations = []
    def add(name, code, mutate):
        changed=copy.deepcopy(raw);mutate(changed)
        errors=verify(changed,deck,root)
        mutations.append({'name':name,'required':code,'rejected_for_required_reason':any(code in e for e in errors),'errors':errors})
    add('omit_cell','ROSTER',lambda d:d['rows'].pop())
    add('duplicate_cell','ROSTER',lambda d:d['rows'].append(copy.deepcopy(d['rows'][0])))
    add('bool_pid','INT_TYPE',lambda d:d['rows'][0]['runtime'].__setitem__('pid',True))
    add('bool_process_exit','PROCESS_EXIT',lambda d:d['rows'][0]['process_receipt'].__setitem__('exit_code',False))
    add('missing_cleanup','CLOSED',lambda d:d['rows'][0].__setitem__('read_fd_closed',False))
    add('altered_pipe_wire','WIRE',lambda d:next(e for r in d['rows'] for e in r['events'] if e['kind']=='read').__setitem__('hex','ff'))
    add('command_payload','COMMAND_TRACE',lambda d:next(e for r in d['rows'] for e in r['events'] if e['kind']=='command').__setitem__('line','wrong'))
    add('wrong_sink_receipt','SINK_JOIN',lambda d:next(e for r in d['rows'] for e in r['events'] if e['kind']=='sink_begin')['receipt'].__setitem__('scheduled_ns',0))
    add('wrong_sample_count','SAMPLE_COUNT',lambda d:d['rows'][0]['samples'].pop())
    add('wrong_owner','OWNER_THREAD',lambda d:d['rows'][0]['events'][0].__setitem__('thread_id',0))
    return mutations


def main():
    p=argparse.ArgumentParser();p.add_argument('deck',type=Path);p.add_argument('raw_dir',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    raw=json.loads((a.raw_dir/'RAW.json').read_text());deck=json.loads(a.deck.read_text())
    errors=verify(raw,deck,a.raw_dir);negative=controls(raw,deck,a.raw_dir)
    if not all(c['rejected_for_required_reason'] for c in negative):errors.append('CONTROL_SENSITIVITY')
    outcomes=[{'id':r['case']['id'],'arm':r['case']['arm'],'adapter':r['case']['adapter'],
               'sleep_ns':r['case']['sleep_ns'],'read_limit':r['case']['read_limit'],
               'disposition':r['disposition'],'samples':len(r['samples']),
               'observed_wall_ns':r['end_ns']-r['start_ns']} for r in raw['rows']]
    h=all(r['disposition']==('sample_budget' if r['arm']=='original' and r['sleep_ns'] else 'finish') for r in outcomes)
    result={'method':'PASS_METHOD_SCOPED' if not errors else 'FAIL_METHOD',
            'hypothesis':'H_PASS_SCOPED' if h else 'H_FAIL_SCOPED','rows':len(outcomes),
            'errors':errors,'controls':negative,'outcomes':outcomes,
            'producer_imported_or_replayed':False,'infinite_starvation_inferred':False}
    with a.output.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'method':result['method'],'hypothesis':result['hypothesis'],'rows':len(outcomes),'errors':errors,'controls':len(negative)}))
    raise SystemExit(1 if errors else 0)


if __name__=='__main__':
    main()
