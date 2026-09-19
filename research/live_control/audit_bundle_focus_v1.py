"""Separate physical stop evidence, failed injection and missing reason evidence."""
import json
from pathlib import Path
from audit_cause_servo_v2 import frames,read
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent;rows=[]
for cohort in ('bundle-focus-01','bundle-focus-02'):
    root=HERE/'results'/cohort;plan=read(root/'plan.json')
    for name,sha in plan['sources'].items():assert digest((HERE/name).read_bytes())==sha
    assert digest((HERE/'results/bundle-pair-01/B/bundle/steps.json').read_bytes())==plan['bundle_source_sha256']
    for name,target,kind in plan['cases']:
        directory=root/name;r=read(directory/'report.json');events=r['events']
        observed=frames(directory,events)
        terminals=[e for e in events if e['event']=='terminal'];first=terminals[0]
        injected=r.get('physical_down_verified') is True and r.get('physical_release_while_output_blocked') is True
        if not injected:
            assert cohort=='bundle-focus-01' and kind=='key'
            assert r['success'] is False and r['error']=="AssertionError('target admission not reached')"
            assert first['status']=='completed' and first['steps_completed']==9 and first['interruption'] is None
            rows.append(dict(cohort=cohort,case=name,classification='injector never triggered; not a focus test',
                             exact_frames=len(observed),probe_success=False));continue
        cause=first['interruption']['record']
        assert cause in r['owner_records'] and cause['reason']=='focus_changed' and cause['verified']
        assert not cause['buttons_down'] and not cause['keys_down']
        assert first['status']=='needs_decision' and first['steps_completed']==target
        assert first['release']['verified'] and not first['release']['buttons_down'] and not first['release']['keys_down']
        current=None;admissions=[]
        for e in events:
            if e['event']=='step_started':current=(e['id'],e['step'])
            elif e['event'] in ('pointer_admission','input_admission'):
                assert current and current[0]=='bundle' and current[1]<=target
                assert e['admitted_ns']<=cause['verified_ns']
                admissions.append((current,e))
        if kind=='key':
            assert [(e['key']) for _,e in admissions if e['event']=='input_admission']==['Control_L']
            assert first['decision_reason'] is None and r['success'] is False
            assert len(terminals)==1  # Assertion stopped probe before isolation check.
        else:
            assert first['decision_reason']=='focus_changed' and r['success']
            assert len(terminals)==2 and terminals[1]['status']=='completed' and terminals[1]['interruption'] is None
        assert all(v=='close returned' for v in r['cleanup'].values())
        rows.append(dict(cohort=cohort,case=name,classification='physical release and no-tail verified',
                         probe_success=r['success'],exact_frames=len(observed),completed_prefix_steps=target,
                         decision_reason=first['decision_reason'],recorded_cause=cause['reason'],
                         release_to_terminal_ms=(first['terminal_ns']-cause['verified_ns'])/1e6,
                         fresh_observation_isolation_verified=kind=='button'))
output=dict(audit_passed=True,rows=rows,audit_sha256=digest(Path(__file__).read_bytes()),
            limits='Scripted actual X11 backend trials, not live socket/model delivery or complete fault coverage. Original failed probes retained. No rollback/unchanged-task claim; no keyboard fresh-intent check because its assertion aborted that branch.')
out=HERE/'results/bundle-focus-audit-01.json'
with out.open('x') as f:json.dump(output,f,indent=2);f.write('\n')
print(json.dumps(output))
