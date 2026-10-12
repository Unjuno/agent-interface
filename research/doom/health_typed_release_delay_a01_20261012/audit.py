import hashlib,json,statistics
from pathlib import Path
root=Path(__file__).resolve().parent; out=root/'results'; freeze=json.loads((root/'FREEZE.json').read_text()); status=json.loads((out/'run-status.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for rel,digest in freeze['files'].items(): assert sha(root/rel)==digest, f'frozen file changed: {rel}'
report=json.loads((root/'inputs/source-report.json').read_text()); a=report['typed_emit_to_artifact_ready_ms']; i=max(range(len(a)),key=a.__getitem__)
assert sha(root/'inputs/source-report.json')==freeze['retained_report_sha256']
assert freeze['artifact_delay_max_ms']==a[i]==150.031473 and i==118
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
summary={'status':'PASS','n_pairs':len(pairs),'source_report_sha256':freeze['retained_report_sha256'],'monitor_file_sha256':freeze['monitor_file_sha256'],'artifact_delay_ms':freeze['artifact_delay_max_ms'],'early_median_ms':statistics.median(p['early_ms'] for p in pairs),'delayed_median_ms':statistics.median(p['delayed_ms'] for p in pairs),'paired_reduction_median_ms':statistics.median(reductions),'paired_reduction_min_ms':min(reductions),'paired_reduction_max_ms':max(reductions),'per_pair':pairs,'checks':['20/20 WSLc exits=0','10/10 paired differences > 0','all 20 hard-invalidations and verified empty releases','all 20 pending answers ineligible','event ordering checked','frozen source/input hashes match'],'limits':['synthetic in-memory fake X only','wait injected rather than native artifact pipeline','no live GUI/game/physical input or task outcome','WSLc swap limit unsupported warning; resource enforcement beyond reported observations not inferred']}
(out/'audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
