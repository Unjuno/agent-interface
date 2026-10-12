import hashlib,json,statistics
from pathlib import Path
root=Path(__file__).resolve().parent; out=root/'results'; freeze=json.loads((root/'FREEZE.json').read_text()); status=json.loads((out/'run-status.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for rel,digest in freeze['files'].items(): assert sha(root/rel)==digest, f'frozen file changed: {rel}'
report=json.loads((root/'inputs/source-report.json').read_text()); a=report['typed_emit_to_artifact_ready_ms']; i=max(range(len(a)),key=a.__getitem__)
assert sha(root/'inputs/source-report.json')==freeze['retained_report_sha256']
assert freeze['artifact_delay_max_ms']==a[i]==150.031473 and i==118
urgent=report['decisions'][5]
invalidation=urgent['final_action_admission']['policy_invalidation']
final=urgent['final_action_admission']
assert invalidation['sequence']==218 and invalidation['signal']['value']==48
assert invalidation['outcome']['status']=='HARD_INVALIDATED' and invalidation['outcome']['hard_minimum']==51
assert urgent['planner_turn_status']=='interrupted' and urgent['planner_answer_eligible'] is False
assert urgent['cover_terminal_before_plan'] is True
events_path=root/'inputs/runtime-events.jsonl'
retention=json.loads((root/'inputs/retention-manifest.json').read_text())
entry=next(x for x in retention['files'] if x['path']=='runtime/events.jsonl')
raw_events=[json.loads(line) for line in events_path.read_text().splitlines()]
assert retention['allocation_id']=='map01-v39-coast-liveness-live-01'
assert entry['bytes']==events_path.stat().st_size and entry['sha256']==sha(events_path)
assert entry['sha256']=='2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381'
retained_audit=json.loads((root/'inputs/retained-audit-v2.json').read_text())
assert retained_audit['formal_pass'] is True and retained_audit['dynamic_revocation_exposed'] is True
typed=next(x for x in raw_events if x.get('event')=='typed_observation' and x.get('sequence')==218)
full=next(x for x in raw_events if x.get('event')=='observation' and x.get('sequence')==218)
accepted=next(x for x in raw_events if x.get('event')=='accepted' and x.get('id')=='cover-5')
cover_terminal=next(x for x in raw_events if x.get('event')=='terminal' and x.get('id')=='cover-5')
assert typed['signals']['health']['value']==48 and typed['capture_ns']==invalidation['signal']['capture_ns']
assert full['artifact_ready_ns']==55550159931938
assert accepted['steps']==16 and cover_terminal['steps_completed']==11
assert cover_terminal['status']=='cancelled'
owner=cover_terminal['release']
assert owner['verified'] is True and owner['keys_down']==[] and owner['buttons_down']==[]
assert typed['emit_ns']<full['artifact_ready_ns']<=invalidation['monitor_received_ns']<=owner['verified_ns']<=cover_terminal['terminal_ns']<urgent['planner_terminal_observed_ns']
urgent_context={'sequence':218,'cover_id':'cover-5','health':48,'hard_minimum':51,
 'capture_to_typed_ready_ms':report['typed_capture_to_ready_ms'][217],
 'typed_ready_to_emit_ms':report['typed_ready_to_emit_ms'][217],
 'typed_emit_to_artifact_ready_ms':(full['artifact_ready_ns']-typed['emit_ns'])/1e6,
 'capture_to_guard_monitor_ms':(invalidation['monitor_received_ns']-invalidation['signal']['capture_ns'])/1e6,
 'typed_emit_to_guard_monitor_ms':(invalidation['monitor_received_ns']-invalidation['signal']['capture_ns'])/1e6-report['typed_capture_to_ready_ms'][217]-report['typed_ready_to_emit_ms'][217],
 'guard_monitor_to_verified_release_ms':(owner['verified_ns']-invalidation['monitor_received_ns'])/1e6,
 'verified_release_to_terminal_ms':(cover_terminal['terminal_ns']-owner['verified_ns'])/1e6,
 'accepted_steps':accepted['steps'],'completed_steps':cover_terminal['steps_completed'],
 'pending_turn_status':urgent['planner_turn_status'],'pending_answer_eligible':urgent['planner_answer_eligible'],
 'cover_cancelled':cover_terminal['status']=='cancelled','owner_release_verified':owner['verified'],
 'cover_terminal_before_plan':urgent['cover_terminal_before_plan'],
 'new_plan_admitted':final['executor_admission'] is not None}
assert urgent_context['typed_emit_to_artifact_ready_ms']==111.11915
assert round(urgent_context['typed_emit_to_guard_monitor_ms'],6)==117.909998
assert round(urgent_context['guard_monitor_to_verified_release_ms'],6)==32.06227
assert len(status)==20 and all(r['exit_code']==0 for r in status)
by_pair={p:{} for p in range(1,11)}
for row in status:
    by_pair[row['pair']][row['arm']]=row
for p in range(1,11):
    expected=['early','delayed'] if p%2 else ['delayed','early']
    assert [r['arm'] for r in status if r['pair']==p]==expected
pairs=[]
for p,arms in by_pair.items():
    assert set(arms)=={'early','delayed'}
    values={}
    for arm,row in arms.items():
        result=json.loads((out/(row['log'].replace('.log','.json'))).read_text())
        assert result['all_assertions_passed'] is True
        assert result['monitor_module_sha256']==freeze['monitor_file_sha256']
        assert result['monitor_blob']=='PR #8866 eb1367cc3ac1184862c454440a418dcf1add9267'
        assert result['executor']['key_was_down_before_invalidation']
        assert result['trigger']['monitor_status']=='HARD_INVALIDATED'
        assert result['trigger']['monitor_event']['outcome']['reason']=='below_hard_minimum'
        assert result['admission']['monitor_mode']=='health_only' and not result['admission']['grants_input_authority']
        x=result['executor']; t=result['timestamps_ns']
        assert x['owner_release_verified'] and x['release']['verified']
        assert x['release']['keys_down']==[] and x['release']['buttons_down']==[]
        assert x['remaining_keys']==[] and x['remaining_buttons']==[]
        assert not x['pending_answer_eligible'] and x['cancellation_requested']
        assert t['executor_cancel']<t['planner_interrupt']<=t['owner_verified_release']<=t['release_published']<=t['terminal']
        expected_delay=0.0 if arm=='early' else freeze['artifact_delay_max_ms']
        assert x['injected_delay_ms']==expected_delay
        assert result['monitor_module_path'].endswith('/worktree/research/live_control/observable_signal_guard_v2.py')
        values[arm]=x['held_key_to_verified_release_ms']
        log=(out/'logs'/row['log']).read_text(errors='replace')
        assert 'kernel does not support swap limit' in log
    pairs.append({'pair':p,'early_ms':values['early'],'delayed_ms':values['delayed'],'reduction_ms':values['delayed']-values['early']})
reductions=[p['reduction_ms'] for p in pairs]
assert all(d>0 for d in reductions)
assert statistics.median(reductions)>=140
summary={'status':'PASS','n_pairs':len(pairs),'source_report_sha256':freeze['retained_report_sha256'],'monitor_file_sha256':freeze['monitor_file_sha256'],'artifact_delay_ms':freeze['artifact_delay_max_ms'],'early_median_ms':statistics.median(p['early_ms'] for p in pairs),'delayed_median_ms':statistics.median(p['delayed_ms'] for p in pairs),'paired_reduction_median_ms':statistics.median(reductions),'paired_reduction_min_ms':min(reductions),'paired_reduction_max_ms':max(reductions),'per_pair':pairs,'retained_hard_event_context':urgent_context,'checks':['20/20 WSLc exits=0','10/10 paired differences > 0','all 20 hard-invalidations and verified empty releases','all 20 pending answers ineligible','event ordering checked','frozen source/input hashes match','retention manifest authenticates the 634-row live event log','seq-218 live cover cancellation and verified release reconciled before planner terminal'],'limits':['paired comparison is synthetic in-memory fake X and injects delay','retained MAP01 trace is one finite episode, with no MAP01 exit','the retained live row does not record a per-key down-before snapshot at the exact invalidation instant','no claim of repeated reliability, causal survival benefit, or successful bounded recovery','WSLc swap limit unsupported warning; resource enforcement beyond reported observations not inferred']}
(out/'audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
