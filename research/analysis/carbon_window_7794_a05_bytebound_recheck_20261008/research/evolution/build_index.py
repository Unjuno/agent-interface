"""Rebuild a scoped historical index from archived results; never rerun actions."""
import csv,hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
LIVE=HERE.parent/'live_control'
FIELDS=['revision','commit','date','hypothesis','mechanism_added','environments','episodes','success_rate','hard_success_rate','new_failure_classes','known_failure_recurrences','regressions','p50','p95','p99','latency_endpoint','planner_boundaries','accepted_programs','observations','serialization_bytes','actual_tokens_if_available','architecture_changes','architecture_churn_score','best_marginal_gain','decision','evidence','backfill_status','notes','successful_tasks','controlled_episodes','individual_gain','bundle_id','bundle_gain','interaction_effect','complexity_delta','new_core_semantics','net_decision']
SPECS=[
    ('input-owner','936069a',[],8,3,'Independent owner isolates expiry from worker stalls','INPUT_OWNER.md'),
    ('owner-v5','b98f672',['owner-assistant-01','owner-assistant-02'],0,1,'Explicit interactive owner lifecycle','OWNER_SELF_USE.md'),
    ('owner-v6','b98f672',['owner-assistant-03'],0,1,'Explicit task destination in ready message','OWNER_SELF_USE.md'),
    ('focus','ba72180',['focus-assistant-01'],8,3,'Observed focus binds input authority','FOCUS.md'),
    ('recovery','9b9e4a5',['recovery-assistant-01'],4,2,'Observation cannot renew same-program authority','RECOVERY.md'),
    ('pixel-quiet','f49141d',['quiet-assistant-01'],0,2,'Bounded advisory pixel quietness','PIXEL_QUIET.md'),
    ('presentation','7427bdd',['presentation-assistant-01','presentation-assistant-02'],0,1,'Optional lossy stdout selection','PRESENTATION.md'),
]
inputs={}

def read(path,lines=False):
    data=path.read_bytes();inputs[str(path.relative_to(HERE.parent))]=hashlib.sha256(data).hexdigest()
    text=data.decode('utf-8')
    return [json.loads(line) for line in text.splitlines()] if lines else json.loads(text)

def write_csv(name,fields,rows):
    with (HERE/name).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def main():
    rows=[];sessions=[];occurrences=[]
    def occurrence(revision,category,trial,evidence,kind,note,introduced=''):
        occurrences.append(dict(occurrence_id=f'O{len(occurrences)+1:03d}',evaluation_revision=revision,
            introduced_revision=introduced,taxonomy_id=category,trial=trial,evidence=evidence,
            kind=kind,global_discovery_status='unresolved historical ordering',notes=note))
    for revision,commit,names,controlled,churn,mechanism,report in SPECS:
        successes=0;observations=0;programs=0;apps=set()
        for name in names:
            folder=LIVE/'results'/name
            events=read(folder/'events.jsonl',True)
            ready=next(e for e in events if e['event']=='ready')
            score=next(e for e in events if e['event']=='independent_evaluation')
            audit=read(folder/'audit.json')
            nobs=sum(e['event']=='observation' for e in events)
            terminals=[e for e in events if e['event']=='terminal']
            assert nobs==audit['exact_frames'] and score['success']==audit['task_success']
            assert all(e['release']['verified'] for e in terminals)
            apps.add(ready['app']);successes+=int(score['success']);observations+=nobs;programs+=len(terminals)
            sessions.append(dict(revision=revision,trial=name,app=ready['app'],success=int(score['success']),observations=nobs,accepted_programs=len(terminals),evidence=str((folder/'events.jsonl').relative_to(HERE.parent))))
            if name=='owner-assistant-02':
                assert score['actual']==[196,None] and score['success'] is False
                occurrence(revision,'F14',name,str((folder/'events.jsonl').relative_to(HERE.parent)),
                    'observed_task_failure','A2 empty; B1 selection documented by screen and report. No proven prior invariant regression.')
        row=dict(revision=revision,commit=commit,date='2026-09-13',mechanism_added=mechanism,
            environments=';'.join(sorted(apps)) if apps else 'private X11 controlled probes',
            episodes=len(names) if names else '',successful_tasks=successes if names else '',
            controlled_episodes=controlled,success_rate=successes/len(names) if names else '',
            hard_success_rate=successes/len(names) if names else '',accepted_programs=programs if names else '',
            observations=observations if names else '',architecture_changes=mechanism,architecture_churn_score=churn,
            decision='HOLD',evidence='../live_control/'+report,backfill_status='scoped retrospective; not full history',
            notes='Success denominators cover listed self-use tasks only; controls are separate. Churn is reviewer judgment. Empty values unknown. Accepted programs are not planner boundaries.')
        rows.append(row)
    for r in read(LIVE/'results/stalls-02/summary.json'):
        if not r['isolated']:
            assert r['first_observed_up_after_deadline_ms']>300
            trial=f"{r['seed']}-{r['fault']}-0"
            occurrence('input-owner','F03',trial,'live_control/results/stalls-02/'+trial+'/report.json',
                'observed_control_failure','Prior cooperative backend: delayed release under injected stall; not a candidate regression.')
    for r in read(LIVE/'results/focus-01/summary.json'):
        if r['focus_changed'] and not r['guarded']:
            assert r['sink_keypresses']
            trial=f"{r['seed']}-1-0"
            occurrence('focus','F04',trial,'live_control/results/focus-01/'+trial+'/report.json',
                'observed_control_failure','Baseline letter reached test sink; event delivery supported by probe report, not raw X event archive.')
    for r in read(LIVE/'results/focus-recovery-01/summary.json'):
        if not r['candidate']:
            assert r['recovery_status']=='needs_decision'
            trial=f"{r['seed']}-0"
            occurrence('recovery','F10',trial,'live_control/results/focus-recovery-01/'+trial+'/report.json',
                'observed_regression','Focus guard blocks observe-only recovery; one regression class, two episodes. Introduced earlier, measured here.','focus')
    for row in rows:
        # Only this particular introduced regression is audited. Other rows stay unknown.
        if row['revision']=='focus':row['regressions']=1
    write_csv('evolution.csv',FIELDS,rows)
    write_csv('sessions.csv',list(sessions[0]),sessions)
    write_csv('occurrences.csv',list(occurrences[0]),occurrences)
    for row in occurrences:assert (HERE.parent/row['evidence']).exists()
    result=dict(indexed_revisions=len(rows),self_use_tasks=len(sessions),successful_self_use_tasks=sum(r['success'] for r in sessions),
        scoped_failure_occurrences=len(occurrences),represented_failure_classes=sorted({r['taxonomy_id'] for r in occurrences}),
        global_discoveries_audited=False,freeze_qualifying_revisions=0,source_sha256=inputs)
    (HERE/'backfill-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))

if __name__=='__main__':main()
