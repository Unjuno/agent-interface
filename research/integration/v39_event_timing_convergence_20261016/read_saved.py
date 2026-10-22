"""Independent saved JSON/source readback; imports no repository runtime."""
import copy,hashlib,json,sys
from pathlib import Path
FIELDS=('typed_ready_ns','emit_ns','stdout_handoff_started_ns','controller_parsed_ns',
        'controller_enqueued_ns','controller_dequeued_ns','controller_monitor_started_ns','controller_monitor_finished_ns')
LABELS=('typed_ready_to_emit_call_ms','producer_pre_handoff_ms','stdout_handoff_to_controller_parse_ms',
        'controller_parse_to_enqueue_ms','controller_queue_wait_ms','controller_dispatch_to_monitor_ms','controller_monitor_service_ms')
CASES={'composed-emitter-dispatch','control-failure','duplicate-json','monitor-error','dispatch','complete-and-missing','invalid-stages'}
def require(value,message):
    if not value:raise ValueError(message)
def summary(events):
    rows=[]
    for event in events:
        if type(event) is not dict or event.get('event')!='typed_observation':continue
        values=[event.get(k) for k in FIELDS]
        good=all(type(v) is int for v in values) and all(a<=b for a,b in zip(values,values[1:]))
        intervals={label:(b-a)/1e6 if type(a) is int and type(b) is int and b>=a else None for label,a,b in zip(LABELS,values,values[1:])}
        rows.append(dict(sequence=event.get('sequence'),**dict(zip(FIELDS,values)),stage_order_valid=good,intervals_ms=intervals))
    return rows
def validate(report,frozen):
    require(report['tests']==70 and report['failures']==0 and report['errors']==0 and report['skips']==[],'suite result')
    require(len(report['modules'])==10 and len(set(report['modules']))==10,'module inventory')
    require(len(report['test_ids'])==70 and len(set(report['test_ids']))==70,'test inventory')
    require(set(report['source_sha256_lf'])==set(frozen),'source inventory')
    for name,pin in report['source_sha256_lf'].items():require(hashlib.sha256(frozen[name]).hexdigest()==pin,'source hash '+name)
    rows=report['rows'];require(len(rows)==7 and {x['case'] for x in rows}==CASES,'row inventory')
    by={x['case']:x for x in rows}
    for case in ('dispatch','composed-emitter-dispatch'):
        row=by[case];events=row.get('events',[row.get('event')])
        require(row['summary']==summary(events),'summary '+case)
        require(row['summary'][0]['stage_order_valid'] is True,'ordered '+case)
    row=by['composed-emitter-dispatch'];require(len(row['events'])==len(row['stdout'])==1,'composed inventory')
    event=row['events'][0];stdout=json.loads(row['stdout'][0]);logs=row['raw_logs']
    require(set(logs)=={'events.jsonl','delivered.jsonl'} and logs['events.jsonl']==logs['delivered.jsonl'],'logs')
    logged=json.loads(logs['events.jsonl']);require('stdout_handoff_started_ns' not in logged,'log boundary')
    require({k:v for k,v in stdout.items() if k!='stdout_handoff_started_ns'}==logged,'stdout/log join')
    require({k:v for k,v in event.items() if not k.startswith('controller_')}==stdout,'controller/stdout join')
    row=by['complete-and-missing'];require(row['summary']==summary(row['events']),'partial summaries')
    require([r['stage_order_valid'] for r in row['summary']]==[True,False],'missing stages')
    row=by['monitor-error'];require(row['primary_preserved'] is True and row['errors']==[],'primary monitor error')
    event=row['event'];require(type(event['controller_monitor_started_ns']) is int and type(event['controller_monitor_finished_ns']) is int and event['controller_monitor_finished_ns']>=event['controller_monitor_started_ns'],'exception finish stamp')
    row=by['duplicate-json'];require(row['events']==[] and row['queue_empty'] is True and len(row['errors'])==1 and 'duplicate JSON member' in row['errors'][0],'duplicate refused')
    row=by['control-failure'];require(row['refused'] is True and row['called']==[] and row['event']['task_effect']=='unknown' and row['event']['release_obligation']['verified'] is False,'control failure refused')
    row=by['invalid-stages'];require(len(row['cases'])==2,'invalid case count')
    for cell in row['cases']:
        expected=summary([cell['event']])[0];require(cell['summary']==expected and expected['stage_order_valid'] is False and None in expected['intervals_ms'].values(),'invalid stages')
    return True
def main():
    q=Path(__file__).resolve().parent
    original=json.loads((q/'original-candidate/index.json').read_text(encoding='utf-8'))
    require(original['head_sha']=='598109fd6329ef88ec469557ae4beae2a2ef3002' and len(original['files'])==6,'original candidate inventory')
    for pin in original['files'].values():require(hashlib.sha256((q/pin['path']).read_bytes()).hexdigest()==pin['sha256'],'original candidate hash')
    index=json.loads((q/'source-index.json').read_text(encoding='utf-8'))
    frozen={name:(q/path).read_bytes() for name,path in index.items()}
    results=[]
    for mode in ('normal','optimized'):
        report=json.loads((q/f'final-{mode}.json').read_text(encoding='utf-8'));validate(report,frozen)
        require(report['optimize']==(mode=='optimized'),'mode')
        rejected=[]
        def reject(name,mutate):
            changed=copy.deepcopy(report);mutate(changed)
            try:validate(changed,frozen)
            except (ValueError,KeyError,TypeError):rejected.append(name)
            else:raise ValueError('mutant accepted '+name)
        def row(r,case):return next(x for x in r['rows'] if x['case']==case)
        reject('duplicate-row',lambda r:r['rows'].append(copy.deepcopy(r['rows'][0])))
        reject('erased-source',lambda r:r['source_sha256_lf'].pop(next(iter(r['source_sha256_lf']))))
        reject('wrong-suite',lambda r:r.update(tests=0))
        reject('lost-primary',lambda r:row(r,'monitor-error').update(primary_preserved=False))
        reject('accept-duplicate-json',lambda r:row(r,'duplicate-json').update(errors=[]))
        reject('accept-control-failure',lambda r:row(r,'control-failure').update(refused=False))
        reject('erase-log',lambda r:row(r,'composed-emitter-dispatch')['raw_logs'].pop('delivered.jsonl'))
        reject('erase-handoff',lambda r:row(r,'composed-emitter-dispatch')['events'][0].pop('stdout_handoff_started_ns'))
        reject('false-complete',lambda r:row(r,'complete-and-missing')['summary'][1].update(stage_order_valid=True))
        reject('wrong-interval',lambda r:row(r,'dispatch')['summary'][0]['intervals_ms'].update(controller_queue_wait_ms=-1))
        changed=dict(frozen);name=next(iter(changed));changed[name]+=b' '
        try:validate(report,changed)
        except ValueError:rejected.append('altered-frozen-source')
        else:raise ValueError('altered source accepted')
        results.append(dict(mode=mode,methods=70,rows=7,source_pins=len(frozen),mutations_rejected=rejected))
    result=dict(decision='PASS_SAVED_READBACK',modes=results,scope='actual extracted Python emitter/reader/wait and local regressions; no GUI/game/provider performance or task qualification')
    Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
