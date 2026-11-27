"""Offline cancellation-boundary audit. No runtime/process/input imports."""
import base64
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def require(value,reason):
    if not value:raise ValueError(reason)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def audit(data,mode):
    require((data['tests'],data['failures'],data['errors'],data['skipped'],data['optimize'])==(3,0,0,0,mode),'suite')
    rows={r['case']:r for r in data['rows']}
    require(len(data['rows'])==3 and set(rows)=={'local-paused-cancel','remote-paused-cancel','remote-normal'},'inventory')
    for name,digest in data['source_sha256_lf'].items():
        require(sha((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))==digest,'source '+name)
    pids=[]
    for case,row in rows.items():
        terminal=row['terminal'];paused=row.get('paused')
        require(terminal['status']==('completed' if case.endswith('normal') else 'cancelled'),'terminal')
        require(terminal['release']['verified'] is True,'eventual cleanup')
        if paused:
            require(paused['parent_cancel'] and paused['worker_alive'] and not paused['resume_set'],'controlled pause')
            require(paused['observed_at_ns']-paused['cancelled_at_ns']>=250_000_000,'fixed window')
            releases=[e for e in row['records'] if e.get('event')=='owner_release' and e.get('reason')=='cancelled']
            require(len(releases)==1,'cancelled release evidence')
            release=releases[0]
            require(paused['observed_at_ns']<release['valid_until_ns'],'not expiry')
            require(release['verified'] and release['keys_down']==[] and release['keys_unknown']==[],'release state')
            require(release['target_process_identity']==[1,41,'a'*64,release['valid_until_ns']],'original source')
            if case.startswith('local'):
                require(paused['local_down']==[] and paused['parent_interruption'] is not None,'local positive control')
                require(release['verified_ns']<=paused['observed_at_ns'],'local released before observation')
            else:
                require(paused['parent_interruption'] is None,'missing parent cause')
                require([e['event'] for e in paused['edges']]==[2],'remote unreleased in window')
                require(not any(e.get('event')=='input_released' for e in paused['events']),'no early release telemetry')
                require(release['verified_ns']>paused['observed_at_ns'],'remote release after resume')
        if case.startswith('local'):continue
        require(row['metadata_shim_only'] is True,'no adapter adoption')
        startup=row['startup'];report=row['service_report'];files={}
        for name,item in row['files'].items():
            raw=base64.b64decode(item['bytes_b64'],validate=True)
            require(sha(raw)==item['sha256'],'raw '+name);files[name]=raw
        require(json.loads(files['startup.json'])==startup,'private startup')
        require(startup['python_optimize']==mode and startup['display']==':fake','child condition')
        require(startup['supervisor_pid']==data['parent_pid'],'supervisor')
        require(startup['pid']==row['spawn_pid'] or startup['parent_pid']==row['spawn_pid'],'owned lineage')
        for name,digest in startup['source_sha256_lf'].items():
            require(sha((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))==digest,'child source')
        pids.extend((row['spawn_pid'],startup['pid']))
        recovery=json.loads(files['recovery.json']);finish=json.loads(files['finish.json'])
        identity={k:startup[k] for k in ('service_id','display','pid','parent_pid','supervisor_pid','owner_id')}
        require(recovery['identity']==finish['identity']==identity,'identity')
        require(recovery['startup_sha256']==finish['startup_sha256']==sha(files['startup.json']),'startup hash')
        require(finish['recovery_sha256']==sha(files['recovery.json']),'recovery hash')
        require(recovery['verified'] and finish['verified'] and finish['initial_verification'] and finish['owner_thread_stopped'],'saved service finish')
        require(report['recovery']==recovery and report['finish']==finish and report['verified'] and report['exit_code']==0 and not report['process_alive'],'joined service exit')
        edges=[json.loads(line) for line in files['fixture-edges.jsonl'].splitlines()]
        require(edges==row['edges'] and [e['event'] for e in edges]==[2,3],'actual edges')
        require(all(e['pid']==startup['pid'] for e in edges),'service edge source')
        if paused:require(edges[0]['at_ns']<paused['cancelled_at_ns']<paused['observed_at_ns']<edges[1]['at_ns'],'remote edge timing')
    return sorted(set(pids))


def main():
    result=[]
    for mode,label in ((0,'normal'),(1,'optimized')):
        data=json.loads((HERE/f'first-{label}.json').read_text());pids=audit(data,mode);rejected=[]
        for kind in ('missing','duplicate','raw','source','cancel','expiry','early-release','late-local','exit'):
            bad=copy.deepcopy(data);rows={r['case']:r for r in bad['rows']};remote=rows['remote-paused-cancel']
            if kind=='missing':bad['rows'].pop()
            elif kind=='duplicate':bad['rows'][-1]=bad['rows'][0]
            elif kind=='raw':remote['files']['startup.json']['bytes_b64']='e30='
            elif kind=='source':remote['startup']['pid']=-1
            elif kind=='cancel':remote['paused']['parent_cancel']=False
            elif kind=='expiry':remote['paused']['observed_at_ns']=10**30
            elif kind=='early-release':remote['paused']['edges'].append({'event':3})
            elif kind=='late-local':rows['local-paused-cancel']['paused']['local_down']=[38]
            elif kind=='exit':remote['service_report']['process_alive']=True
            try:audit(bad,mode)
            except (ValueError,KeyError):rejected.append(kind)
            else:raise ValueError('accepted mutant '+kind)
        result.append(dict(mode=mode,rows=3,source_pins=len(data['source_sha256_lf']),owned_pids=pids,rejected_mutants=rejected))
    print(json.dumps(dict(scope='saved data only; no runtime execution',decision='reject metadata-only owner substitution; independent cancellation/cause relay required',results=result),indent=2))


if __name__=='__main__':main()
