"""Retrospective same-process timing decomposition; not a paired performance study."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
RESEARCH=HERE.parent
COHORTS={
    'inkscape':'live_control/results/pointer-desktop-01',
    'openttd':'openttd_task/results/guard-self-use-01',
    'mindustry':'benchmark_discovery/results/mindustry-build-self-use-01',
}
COMMON=['live_control/'+p for p in ('session_v9.py','session_v8.py','session_v7.py',
    'session_v6.py','session_v5.py','session_v4.py','input_owner_v5.py','executor_v3.py','lease.py')]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())

def decompose(events):
    obs=[r for r in events if r['event']=='observation']
    accepted=[r for r in events if r['event']=='accepted']
    terminals=[r for r in events if r['event']=='terminal']
    if not obs or not accepted or len(accepted)!=len(terminals):raise ValueError('incomplete episode')
    if [r['id'] for r in accepted]!=[r['id'] for r in terminals]:raise ValueError('unmatched order')
    start=obs[0]['capture_ns'];end=terminals[-1]['terminal_ns']
    if any(type(t) is not int for t in [start,end,*[r['accepted_ns'] for r in accepted],*[r['terminal_ns'] for r in terminals]]):
        raise ValueError('integer timestamps required')
    gaps=[accepted[0]['accepted_ns']-start]
    gaps += [b['accepted_ns']-a['terminal_ns'] for a,b in zip(terminals,accepted[1:])]
    active=[b['terminal_ns']-a['accepted_ns'] for a,b in zip(accepted,terminals)]
    if any(n<0 for n in gaps+active) or end<=start:raise ValueError('reversed or overlapping intervals')
    if sum(gaps)+sum(active)!=end-start:raise ValueError('partition mismatch')
    return {'capture_to_last_terminal_s':(end-start)/1e9,
            'admitted_execution_s':sum(active)/1e9,'outside_admitted_execution_s':sum(gaps)/1e9,
            'outside_fraction':sum(gaps)/(end-start),'initial_to_first_admission_s':gaps[0]/1e9,
            'between_program_gaps_s':[x/1e9 for x in gaps[1:]],
            'program_execution_s':[x/1e9 for x in active],
            'accepted_programs':len(accepted),'observations':len(obs),
            'rejected_requests':sum(r['event']=='rejected' for r in events)}

def main():
    out=HERE/'results/pointer-timeline-01';out.mkdir(parents=True,exist_ok=False)
    rows={};inputs={};common=None
    for domain,relative in COHORTS.items():
        root=RESEARCH/relative
        source_file=root/('sources.json' if domain=='inkscape' else 'manifest.json')
        sources=read(source_file)
        if domain!='inkscape':sources=sources['sources']
        selected={name:sources[name] for name in COMMON}
        for name,digest in selected.items():assert sha(RESEARCH/name)==digest,name
        if common is None:common=selected
        assert selected==common,'backend differs across domains'
        event_file=root/'events.jsonl'
        events=[json.loads(line) for line in event_file.read_text().splitlines()]
        value=decompose(events)
        assert all(e['status']=='completed' and e['release']['verified'] is True for e in events if e['event']=='terminal')
        evaluation=next(e for e in events if e['event']=='independent_evaluation')
        assert evaluation.get('contract_satisfied',evaluation.get('success')) is True
        rows[domain]={'cohort':relative,**value,'task_contract_passed':True,
                      'model_identity':None,'model_tokens':None,'model_receipt_ns':None}
        inputs[str(event_file.relative_to(RESEARCH))]=sha(event_file)
        inputs[str(source_file.relative_to(RESEARCH))]=sha(source_file)
    # Synthetic chronology controls prevent malformed partitions from looking fast.
    controls={}
    seed=[{'event':'observation','capture_ns':10},{'event':'accepted','id':'a','accepted_ns':20},
          {'event':'terminal','id':'a','terminal_ns':30}]
    for name,change in [('negative',lambda x:x[1].update(accepted_ns=5)),
                        ('identity',lambda x:x[2].update(id='b')),
                        ('type',lambda x:x[2].update(terminal_ns=True))]:
        case=json.loads(json.dumps(seed));change(case)
        try:decompose(case)
        except ValueError as exc:controls[name]=str(exc)
        else:raise AssertionError(name)
    report={'scope':'retrospective bottleneck evidence only; distinct tasks and adapters; no pooled gain',
            'clock_scope':'within each originating runtime process, no cross-process subtraction',
            'outside_meaning':'all time outside accepted-to-terminal intervals, including decisions, transport, review, rejection and other work; not model inference time',
            'common_source_hashes':common,'input_hashes':inputs,'domains':rows,'controls':controls,
            'source_sha256':sha(Path(__file__))}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
