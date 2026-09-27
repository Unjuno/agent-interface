"""Read-only reconstruction; imports no worker, runner or validator."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent


def sha(b):
    return hashlib.sha256(b).hexdigest() if b is not None else None


def expected(f, slot):
    status = f['status']
    r = dict(schema='agent-interface/static-program-validation-v1', status=status,
             static_valid=True if status=='valid' else False if status=='invalid' else None,
             side_effect_authority=False,runtime_admission='not_evaluated',
             backend_checked=False,task_success=None)
    if f['content'] is not None:
        r['input_sha256'] = sha(f['content'].encode('utf-8'))
    if status == 'valid':
        r.update(source_operation_count=1 if slot==7 else 2,
                 expanded_operation_count={0:2,2:2,5:4,7:1}[slot],
                 compilation='bounded_text_gap' if slot==5 else None,
                 required_capabilities=(['capture.frame','display.geometry','input.release_all']
                                        if slot in (0,2) else
                                        ['clock.monotonic','event.feedback','input.release_all','input.text']
                                        if slot==5 else ['input.release_all']))
    else:
        r['error'] = f['error']
        if f['detail'] is not None:
            r['detail'] = f['detail']
        if slot==1:
            r.update(detail_source='program_validation',compilation=None,
                     expanded_operation_index=0,source_operation_index=0)
        elif slot==6:
            r.update(detail_source='sequence_expansion')
        elif slot==4:
            r.update(line=2,column=1)
    return r


def audit_records(records, fixtures, count, construction=False):
    errors=[]; checks=0
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok: errors.append(label)
    order=[]
    for trial in ([-1] if construction else range(-1,7)):
        for mode in (['fresh','resident'] if trial%2==0 else ['resident','fresh']):
            order.append((trial,mode))
    check(len(records)==len(order),'denominator')
    output_count=process_count=0
    by_pair={}
    for index,r in enumerate(records):
        tag=str(index)
        check(index<len(order) and (r['trial'],r['mode'])==order[index],tag+':order')
        check(r['phase']==('warmup' if r['trial']==-1 else 'measured'),tag+':phase')
        check(r['count']==count and r['status']=='COMPLETE',tag+':complete')
        check(len(r['responses'])==count,tag+':responses')
        processes=r['processes']
        check(len(processes)==(count if r['mode']=='fresh' else 1),tag+':process_count')
        check(len(r['affinity'])==1 and type(r['affinity'][0]) is int,tag+':affinity')
        check(r['argv'][1:4]==['-I','-S','-B'] and r['argv'][-1].endswith('/worker.py'),tag+':command')
        check(type(r['start_ns']) is int and type(r['end_ns']) is int and r['end_ns']>r['start_ns'],tag+':time')
        check(type(r['children_cpu_ns']) is int and r['children_cpu_ns']>=0,tag+':cpu')
        check(json.loads(r['stdin'])==str(Path(r['cwd'])/'input.json'),tag+':stdin')
        for j,p in enumerate(processes):
            check(type(p['pid']) is int and p['pid']>0 and p['exit']==0 and p['stderr']=='' and p['tail']=='',tag+f':exit{j}')
        previous=r['start_ns']
        for j,response in enumerate(r['responses']):
            key=tag+f':response{j}'; slot=j%8; f=fixtures[slot]
            check(response['step']==j and response['fixture']==slot,key+':slot')
            pid=processes[j if r['mode']=='fresh' else 0]['pid'] if processes else None
            check(response['pid']==pid,key+':pid')
            check(previous<=response['prepare_start_ns']<=response['request_start_ns']<response['response_end_ns']<=r['end_ns'],key+':clock_order')
            previous=response['response_end_ns']
            h=sha(f['content'].encode('utf-8')) if f['content'] is not None else None
            check(response['input_sha256']==h and response['after_sha256']==h,key+':input_identity')
            value=json.loads(response['stdout'])
            check(value==expected(f,slot),key+':report')
            check(response['stdout']==json.dumps(value,ensure_ascii=True,sort_keys=True)+'\n',key+':wire')
            if r['phase']=='measured':output_count+=1
        by_pair[(r['trial'],r['mode'])]=r
        if r['phase']=='measured':process_count+=len(processes)
    for trial in ([-1] if construction else range(-1,7)):
        a=by_pair.get((trial,'fresh'));b=by_pair.get((trial,'resident'))
        check(a is not None and b is not None,f'pair{trial}:present')
        if a and b:
            check([x['stdout'] for x in a['responses']]==[x['stdout'] for x in b['responses']],f'pair{trial}:parity')
    stats={}
    if not construction and not errors:
        ratios=[]
        for mode in ('fresh','resident'):
            rs=[by_pair[(i,mode)] for i in range(7)]
            def summary(values):return dict(median=statistics.median(values),minimum=min(values),maximum=max(values))
            stats[mode]=dict(total_ms=summary([(r['end_ns']-r['start_ns'])/1e6 for r in rs]),
                            first_ms=summary([(r['responses'][0]['response_end_ns']-r['start_ns'])/1e6 for r in rs]),
                            children_cpu_ms=summary([r['children_cpu_ns']/1e6 for r in rs]))
            if count>1:
                stats[mode]['warm_response_ms']=summary([(x['response_end_ns']-x['request_start_ns'])/1e6 for r in rs for x in r['responses'][1:]])
        for i in range(7):
            a=by_pair[(i,'fresh')];b=by_pair[(i,'resident')]
            ratios.append((b['end_ns']-b['start_ns'])/(a['end_ns']-a['start_ns']))
        stats['paired_ratios']=ratios
        stats['paired_ratio_median']=statistics.median(ratios)
    return dict(checks=checks,errors=errors,count=count,responses=output_count,processes=process_count,stats=stats)


def main():
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--construction',action='store_true');a=p.parse_args()
    fixtures=json.loads((ROOT/'FIXTURES.json').read_text())
    batches=[a.directory] if a.construction else [a.directory/f'n{n}' for n in (1,8,32)]
    results=[]; errors=[];checks=0
    for b in batches:
        rows=[json.loads(line) for line in (b/'RAW.jsonl').read_text().splitlines()]
        result=audit_records(rows,fixtures,rows[0]['count'],a.construction);results.append(result)
        checks+=result['checks'];errors.extend(result['errors'])
        if not a.construction:
            launch=json.loads((b/'LAUNCHER.json').read_text())
            checks+=1
            if launch['exit']!=0 or launch['timeout'] or launch['stderr']!='':errors.append(str(b)+':launcher')
    if not a.construction:
        for name,h in json.loads((ROOT/'FREEZE.json').read_text()).items():
            checks+=1
            if sha((ROOT/name).read_bytes())!=h:errors.append('source:'+name)
    speed=all(r['stats'].get('paired_ratio_median',999)<=.5 for r in results if r['count']>1)
    decision='FAIL_EVIDENCE' if errors else 'PASS_CONSTRUCTION' if a.construction else 'PASS_RESIDENT_STATIC_VALIDATION_COST_SCOPED' if speed else 'HOLD_COST_TRADEOFF'
    print(json.dumps(dict(decision=decision,checks=checks,errors=errors,batches=results),sort_keys=True,indent=2))
    return int(bool(errors))


if __name__=='__main__':
    raise SystemExit(main())
