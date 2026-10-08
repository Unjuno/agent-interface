"""Raw-only oracle; never imports actor, runner or a SQLite cancellation policy."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile

STATES = ('IDLE','IMPLICIT_ONE','EXPLICIT_ONE','EXPLICIT_DONE','IMPLICIT_TWO')
MODES = ('INTERRUPT_ONLY','AWAIT_TARGET','FINALIZE_ALL')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def expected_busy(state, mode):
    if state == 'IDLE' or mode == 'FINALIZE_ALL':
        return False
    return mode == 'INTERRUPT_ONLY' or state != 'IMPLICIT_ONE'


def inspect_snapshot(snapshot):
    if set(snapshot) != {'','-wal','-shm'}:
        raise ValueError('snapshot members')
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory)/'db'
        sizes = {}
        for suffix, encoded in snapshot.items():
            if encoded is not None:
                data = base64.b64decode(encoded,validate=True)
                if len(data)>1_000_000:
                    raise ValueError('snapshot bound')
                Path(str(db)+suffix).write_bytes(data)
                sizes[suffix] = len(data)
            else:
                sizes[suffix] = None
        with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=0) as con:
            rows = [list(x) for x in con.execute('SELECT i,v FROM t ORDER BY i')]
            integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
        con.close()
    return rows, sizes, integrity


def audit_records(records, kind):
    errors, count = [], 0
    summary = {m:{'cases':0,'primary_busy':0,'target_interrupts':0,'interrupt_and_busy':0} for m in MODES}
    def ck(condition, label):
        nonlocal count
        count += 1
        if not condition:
            errors.append(label)
    schedule = [(s,m,r) for s in STATES for m in MODES for r in range(2 if kind=='formal' else 1)]
    n = 64 if kind=='formal' else 16
    ck(len(records)==len(schedule),'record_count')
    for index, (record, (state,mode,rep)) in enumerate(zip(records,schedule)):
        label = str(index)+':'
        try:
            ck(record['state']==state and record['mode']==mode and type(record['rep']) is int and record['rep']==rep,label+'schedule')
            batch = index//10 if kind=='formal' else 0
            ci = index%10 if kind=='formal' else index
            ck(record['id']==f'{kind}-b{batch}-c{ci}',label+'identity')
            ck(record['complete'] is True and 'error' not in record,label+'complete')
            ck(record['authority_granted'] is False and record['task_success'] is None,label+'authority')
            ck(type(record['n']) is int and record['n']==n,label+'n')
            expected = [] if state=='IDLE' else [[[i,i] for i in range(n)]] if state=='EXPLICIT_DONE' else [[[0,0]]]* (2 if state=='IMPLICIT_TWO' else 1)
            ck(record['arm']['copies']==expected,label+'prefix')
            ck(record['cancel']['copies']==expected and record['cleanup']['copies']==expected,label+'retained_prefix')
            cursor_count = 0 if state=='IDLE' else 2 if state=='IMPLICIT_TWO' else 1
            ck(record['arm']['cursor_count']==cursor_count,label+'cursor_count')
            ck(record['arm']['in_transaction'] is state.startswith('EXPLICIT'),label+'arm_txn')
            ck(record['init']=={'journal':'wal','checkpoint':[0,0,0],'n':n},label+'init')
            ck(record['update']=={'value':9999},label+'update')
            cancel = record['cancel']
            ck(cancel['interrupt_returned'] is True,label+'interrupt_return')
            ck(cancel['tail']==[],label+'tail')
            interrupted = mode=='AWAIT_TARGET' and state in ('IMPLICIT_ONE','EXPLICIT_ONE','IMPLICIT_TWO')
            target_error = cancel['target_error']
            ck((isinstance(target_error,dict) and type(target_error.get('code')) is int and target_error['code']==9 and target_error.get('name')=='SQLITE_INTERRUPT' and target_error.get('type')=='OperationalError') if interrupted else target_error is None,label+'target_error')
            ck(type(cancel['closed']) is int and cancel['closed']==(cursor_count if mode=='FINALIZE_ALL' else 0),label+'closed_count')
            ck(cancel['rollback'] is (mode=='FINALIZE_ALL' and state.startswith('EXPLICIT')),label+'rollback')
            ck(cancel['in_transaction'] is (mode!='FINALIZE_ALL' and state.startswith('EXPLICIT')),label+'cancel_txn')
            busy = expected_busy(state,mode)
            primary = record['primary']
            cp = primary['checkpoint']
            ck(isinstance(cp,list) and len(cp)==3 and all(type(x) is int for x in cp),label+'checkpoint_types')
            ck(cp==([1,1,0] if busy else [0,0,0]),label+'primary_checkpoint')
            ck(type(primary['wal_bytes']) is int and (primary['wal_bytes']>0 if busy else primary['wal_bytes']==0),label+'primary_extent')
            ck(record['cleanup']['in_transaction'] is False,label+'cleanup_txn')
            ck(record['after_cleanup']=={'checkpoint':[0,0,0],'wal_bytes':0},label+'cleanup_checkpoint')
            ck(set(record['snapshots'])=={'initial','updated','primary','cleanup','final'},label+'snapshot_set')
            for stage in ('initial','updated','primary','cleanup','final'):
                try:
                    data,sizes,integrity = inspect_snapshot(record['snapshots'][stage])
                    values = [[i,9999 if i==0 and stage!='initial' else i] for i in range(n)]
                    ck(data==values and integrity=='ok',label+'db:'+stage)
                    if stage=='primary':
                        ck((sizes['-wal'] or 0)==primary['wal_bytes'],label+'wal_binding')
                        if busy:
                            raw = base64.b64decode(record['snapshots'][stage]['-wal'])
                            page = int.from_bytes(raw[8:12],'big')
                            ck(page==4096 and len(raw)==32+cp[1]*(page+24),label+'wal_frame_count')
                    if stage in ('cleanup','final'):
                        ck(sizes['-wal'] in (None,0),label+'empty_wal:'+stage)
                except Exception as error:
                    ck(False,label+'snapshot_decode:'+stage+':'+type(error).__name__)
            expected_ops = {'writer':['INIT','UPDATE','CHECK','CHECK','QUIT'],'reader':['ARM','CANCEL','CLEAN','QUIT']}
            ck(set(record['processes'])==set(expected_ops),label+'roles')
            response_values = {}
            for role, ops in expected_ops.items():
                process = record['processes'][role]
                ck(type(process['exit']) is int and process['exit']==0 and process['forced'] is False,label+'exit:'+role)
                ck(type(process['pid']) is int and process['pid']>0 and process['stderr']=='',label+'pid_stderr:'+role)
                ck(process['start_ns']<process['end_ns'],label+'process_order:'+role)
                ck(process['argv'][-3]==role and Path(process['argv'][-4]).name=='actor.py',label+'argv:'+role)
                ck(len(process['wire'])==len(ops),label+'wire_length:'+role)
                expected_log = []
                times = []
                values = []
                for j,(wire,op) in enumerate(zip(process['wire'],ops)):
                    q,p = json.loads(wire['request']),json.loads(wire['response'])
                    ck(q['op']==op and p['op']==op and p['role']==role and p['pid']==process['pid'],label+f'wire_identity:{role}:{j}')
                    ck(process['start_ns']<=wire['sent_ns']<=p['start_ns']<=p['end_ns']<=wire['received_ns']<=process['end_ns'],label+f'wire_order:{role}:{j}')
                    ck(isinstance(p['sql'],list),label+f'sql_type:{role}:{j}')
                    expected_log.extend([{'recv':wire['request']},{'send':wire['response']}])
                    times.append((wire['sent_ns'],wire['received_ns']))
                    values.append(p['value'])
                    if role=='writer' and op=='CHECK':
                        ck(p['sql']==['PRAGMA wal_checkpoint(TRUNCATE)'],label+f'checkpoint_sql:{j}')
                    if role=='reader' and op=='CANCEL':
                        ck(p['sql']==(['ROLLBACK'] if mode=='FINALIZE_ALL' and state.startswith('EXPLICIT') else []),label+'cancel_sql')
                ck([json.loads(x) for x in process['actor_log'].splitlines()]==expected_log,label+'bilateral_log:'+role)
                ck(all(a[1]<=b[0] for a,b in zip(times,times[1:])),label+'sequential:'+role)
                response_values[role] = values
            ck(response_values['writer'][:4]==[record['init'],record['update'],record['primary'],record['after_cleanup']],label+'writer_join')
            ck(response_values['reader'][:3]==[record['arm'],record['cancel'],record['cleanup']],label+'reader_join')
            w,r = record['processes']['writer']['wire'],record['processes']['reader']['wire']
            ck(w[0]['received_ns']<=r[0]['sent_ns'] and r[0]['received_ns']<=w[1]['sent_ns'] and w[1]['received_ns']<=r[1]['sent_ns'] and r[1]['received_ns']<=w[2]['sent_ns'] and w[2]['received_ns']<=r[2]['sent_ns'] and r[2]['received_ns']<=w[3]['sent_ns'],label+'cross_process_order')
            summary[mode]['cases'] += 1
            summary[mode]['primary_busy'] += int(cp[0]==1)
            summary[mode]['target_interrupts'] += int(target_error is not None)
            summary[mode]['interrupt_and_busy'] += int(target_error is not None and cp[0]==1)
        except (KeyError,TypeError,ValueError,IndexError) as error:
            ck(False,label+'record_shape:'+type(error).__name__)
    return {'decision':'PASS_SQLITE_INTERRUPT_RELEASE_BOUNDARY_SCOPED' if not errors else 'FAIL_OR_HOLD_RAW_INTEGRITY','checks':count,'errors':errors,'summary':summary,'records_sha256':digest(records),'kind':kind}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('kind',choices=['construction','formal'])
    ap.add_argument('directory',type=Path)
    ap.add_argument('--controls',type=Path)
    args = ap.parse_args()
    batches = list(range(3)) if args.kind=='formal' else [0]
    rows, envelope_errors = [], []
    for batch in batches:
        prefix = args.directory/f'batch{batch}'
        try:
            receipt = json.loads(prefix.with_suffix('.execution.json').read_text())
            report = json.loads((prefix/'BATCH.json').read_text())
            batchrows = [json.loads(x) for x in (prefix/'RECORDS.jsonl').read_text().splitlines()]
            if type(receipt['exit']) is not int or receipt['exit']!=0 or receipt['timeout'] is not False or report['pid']!=receipt['pid'] or report['complete'] is not True or report['rows']!=len(batchrows) or report['kind']!=args.kind or report['batch']!=batch:
                envelope_errors.append('batch:'+str(batch))
            if not (receipt['start_ns']<=report['start_ns']<=report['end_ns']<=receipt['end_ns']):
                envelope_errors.append('batch_order:'+str(batch))
            if json.loads(prefix.with_suffix('.stdout').read_text())!=report or prefix.with_suffix('.stderr').read_text()!='':
                envelope_errors.append('batch_output:'+str(batch))
            rows.extend(batchrows)
        except Exception as error:
            envelope_errors.append('batch_read:'+str(batch)+':'+type(error).__name__)
    result = audit_records(rows,args.kind)
    freeze = Path(__file__).with_name('FREEZE.json')
    if args.kind=='formal':
        try:
            hashes = json.loads(freeze.read_text())['sha256']
            for name,expected in hashes.items():
                if hashlib.sha256((freeze.parent/name).read_bytes()).hexdigest()!=expected:
                    envelope_errors.append('source:'+name)
        except Exception as error:
            envelope_errors.append('freeze:'+type(error).__name__)
    result['errors'] += envelope_errors
    result['decision'] = 'PASS_SQLITE_INTERRUPT_RELEASE_BOUNDARY_SCOPED' if not result['errors'] else 'FAIL_OR_HOLD_RAW_INTEGRITY'
    if args.controls:
        if result['errors']:
            raise SystemExit('baseline failed; no controls')
        args.controls.mkdir(parents=True,exist_ok=False)
        targets = [(0,['authority_granted'],True),(0,['processes','reader','exit'],1),(0,['complete'],False),(0,['primary','wal_bytes'],7),(0,['primary','checkpoint'],[1,1,0]),(0,['cancel','interrupt_returned'],False),(0,['n'],999),(0,['id'],'wrong'),(0,['processes','reader','pid'],999),(0,['snapshots','initial',''],base64.b64encode(b'not a database').decode()),(3 if args.kind=='construction' else 6,['arm','copies'],[[[0,999]]]),(4 if args.kind=='construction' else 8,['cancel','target_error','code'],8)]
        verdicts = []
        for i,(idx,path,value) in enumerate(targets):
            changed = copy.deepcopy(rows)
            parent = changed[idx]
            for key in path[:-1]: parent=parent[key]
            previous=parent[path[-1]]; parent[path[-1]]=value
            check=audit_records(changed,args.kind)
            evidence={'index':idx,'path':path,'before':previous,'after':value,'original_sha256':digest(rows),'mutated_sha256':digest(changed),'errors':check['errors'],'changed':digest(rows)!=digest(changed),'rejected':bool(check['errors'])}
            (args.controls/f'c{i:02}.json').write_text(json.dumps(evidence,sort_keys=True)+'\n')
            verdicts.append(evidence)
        output={'baseline':result['decision'],'count':len(verdicts),'changed':sum(v['changed'] for v in verdicts),'rejected':sum(v['rejected'] for v in verdicts),'results':verdicts}
        print(json.dumps(output,sort_keys=True))
        return 0 if output['changed']==output['rejected']==12 else 1
    print(json.dumps(result,sort_keys=True))
    return bool(result['errors'])


if __name__=='__main__':
    raise SystemExit(main())
