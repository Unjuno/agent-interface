"""Offline evidence readback; imports no owner, socket or process implementation."""
import base64
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CASES={'normal','client-death','service-death','blocked-release','context-exit-failure',
       'startup-failure','generation-and-exclusive','export-snapshot','startup-custody',
       'exit-commit-barrier','partial-allocation-custody','publication-fault-custody',
       'blocked-publication-failure'}


def require(value,message):
    if not value:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def audit(data,mode):
    require((data['tests'],data['failures'],data['errors'],data['skipped'],data['optimize'])==(55,0,0,0,mode),'suite outcome')
    rows=data['process_rows']
    require(len(rows)==len(CASES) and {r['case'] for r in rows}==CASES,'case inventory')
    require(len(data['rpc_rows'])==26,'selected RPC row count')
    for path,digest in data['source_sha256_lf'].items():
        require(sha((ROOT/path).read_bytes().replace(b'\r\n',b'\n'))==digest,'source '+path)
    identities=set();pids=set()
    for row in rows:
        case=row['case'];files={}
        for name,item in row.get('files',{}).items():
            raw=base64.b64decode(item['bytes_b64'],validate=True)
            require(sha(raw)==item['sha256'],'raw checksum '+case+'/'+name)
            files[name]=raw
        if case=='export-snapshot':
            require(sha(base64.b64decode(row['bytes_b64']))==row['sha256'],'snapshot');continue
        if case=='startup-custody':
            require(len(row['outcomes'])==3 and all(x['owned_handle_retained'] and x['primary_preserved'] for x in row['outcomes']),'startup custody');continue
        if case=='partial-allocation-custody':
            require([x['closed'] for x in row['outcomes']]==[2,4],'partial cleanup')
            require(all(x['report']['spawn_pid'] is None and not x['report']['verified'] and not x['report']['process_alive'] for x in row['outcomes']),'unstarted receipt');continue
        if case=='publication-fault-custody':
            require(row['order']==['wait','context-exit'] and row['primary_preserved'],'publication custody');continue
        require(row['cleanup']['forced'] is False and row['cleanup']['process_alive'] is False,'cleanup '+case)
        startup=row.get('startup')
        if startup is None:
            require(case=='startup-failure' and not row['report']['verified'] and row['report']['exit_code']!=0,'startup failure')
            failure=json.loads(files['failure.json'])
            require(failure['service_id']==row['service_id'] and (failure['pid']==row['spawn_pid'] or failure['parent_pid']==row['spawn_pid']),'failure lineage')
            pids.update((row['spawn_pid'],failure['pid']));continue
        require(json.loads(files['startup.json'])==startup,'private startup binding')
        require(startup['python_optimize']==mode and startup['display']==':fake','child mode/display')
        require(startup['pid']==row['spawn_pid'] or startup['parent_pid']==row['spawn_pid'],'owned lineage')
        require(startup['parent_pid']==startup['supervisor_pid'] or startup['parent_pid']==row['spawn_pid'],'supervisor lineage')
        require(startup['service_id'] not in identities,'unique generation');identities.add(startup['service_id'])
        pids.update((startup['pid'],row['spawn_pid']))
        for path,digest in startup['source_sha256_lf'].items():
            require(sha((ROOT/path).read_bytes().replace(b'\r\n',b'\n'))==digest,'child source '+path)
        identity={k:startup[k] for k in ('service_id','display','pid','parent_pid','supervisor_pid','owner_id')}
        recovery=json.loads(files['recovery.json']) if 'recovery.json' in files else None
        finish=json.loads(files['finish.json']) if 'finish.json' in files else None
        if recovery:
            require(recovery['identity']==identity and recovery['startup_sha256']==sha(files['startup.json']),'recovery binding')
            core=recovery['core']
            require(core['display']==startup['display'] and core['service_id']==startup['service_id'],'core identity')
            require(recovery['verified']==(core['verified'] is True and recovery['service_error'] is None),'core verification')
            if core['verified']:
                require(core['owner_thread_stopped'] is True,'verified stop')
                require(all(r['verified'] is True for r in core['release_records']),'release records')
        if finish:
            require(recovery is not None and finish['identity']==identity,'finish identity')
            require(finish['startup_sha256']==sha(files['startup.json']) and finish['recovery_sha256']==sha(files['recovery.json']),'finish hashes')
            require(finish['initial_verification'] is recovery['verified'],'initial immutable result')
            require(finish['verified']==(recovery['verified'] is True and finish['context_exit_success'] is True and finish['owner_thread_stopped'] is True and finish['service_error'] is None),'finish verification')
        report=row.get('report',row.get('after'))
        require(report['process_alive'] is False,'terminal process exit')
        expected=finish is not None and finish['verified'] is True and report['exit_code']==0
        require(report['verified'] is expected,'joined receipt')
        if 'recovery' in report:require(report['recovery']==recovery,'report recovery readback')
        if 'finish' in report:require(report['finish']==finish,'report finish readback')
        if 'edges' in row:
            saved=[json.loads(line) for line in files['fixture-edges.jsonl'].splitlines()]
            require(saved==row['edges'] and all(e['pid']==startup['pid'] for e in saved),'edge observation')
            require([e['event'] for e in saved]==([2] if case=='service-death' else [2,3]),'edge sequence')
        if case in ('normal','client-death','generation-and-exclusive','exit-commit-barrier'):require(report['verified'],'positive control')
        if case=='client-death':
            client=row['client_ready'];require(row['client_exit']==73 and client['pid']!=startup['pid'],'client death')
            require(client['pid']==row['client_spawn_pid'] or client['parent_pid']==row['client_spawn_pid'],'client lineage')
            pids.update((client['pid'],row['client_spawn_pid']))
        if case=='exit-commit-barrier':require(row['before']['process_alive'] and row['before']['receipt_verified'] and not row['before']['verified'],'live receipt rejected')
        if case=='blocked-release':
            require(row['before']['process_alive'] and not row['before']['verified'] and not recovery['verified'],'blocked custody')
            require(row['before']['recovery']==recovery and finish['owner_thread_stopped'] and not finish['verified'],'no late upgrade')
        if case in ('service-death','context-exit-failure','blocked-publication-failure'):
            require(not report['verified'] and report['exit_code']!=0 and finish is None,'failure stays failure')
        if case=='context-exit-failure':require(recovery['verified'] and 'failure.json' in files,'context exit evidence')
        if case=='blocked-publication-failure':require(row['before']['process_alive'] and not row['before']['verified'] and recovery is None and 'failure.json' in files,'publication failure custody')
    return sorted(pids)


def main():
    summaries=[]
    for mode,label in ((0,'normal'),(1,'optimized')):
        data=json.loads((HERE/f'final-{label}.json').read_text())
        pids=audit(data,mode);mutants=[]
        for kind in ('missing','duplicate','raw','identity','alive','upgrade','cleanup','publication','initial'):
            bad=copy.deepcopy(data);rows={r['case']:r for r in bad['process_rows']}
            if kind=='missing':bad['process_rows'].pop()
            elif kind=='duplicate':bad['process_rows'][-1]=bad['process_rows'][0]
            elif kind=='raw':rows['normal']['files']['startup.json']['bytes_b64']='e30='
            elif kind=='identity':rows['normal']['startup']['pid']=-1
            elif kind=='alive':rows['normal']['report']['process_alive']=True
            elif kind=='upgrade':rows['blocked-release']['after']['verified']=True
            elif kind=='cleanup':rows['normal']['cleanup']['forced']=True
            elif kind=='publication':rows['blocked-publication-failure']['before']['process_alive']=False
            elif kind=='initial':rows['context-exit-failure']['report']['verified']=True
            try:audit(bad,mode)
            except (ValueError,KeyError):mutants.append(kind)
            else:raise ValueError('accepted mutant '+kind)
        summaries.append(dict(mode=mode,tests=data['tests'],process_rows=len(data['process_rows']),owned_pids=pids,rejected_mutants=mutants))
    print(json.dumps(dict(scope='saved bytes only; no process/input execution',results=summaries),indent=2))


if __name__=='__main__':main()
