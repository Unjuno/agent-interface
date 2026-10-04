"""Test whether wrapper update identity authenticates scorer-value source epoch."""
import json
import platform
import subprocess
import sys
import types
from pathlib import Path

HERE=Path(__file__).resolve().parent
FREEZE=json.loads((HERE/'FREEZE.json').read_text(encoding='utf-8'))
REPO=Path(__file__).resolve().parents[3]

def git(*args):
    return subprocess.run(['git','-C',str(REPO),*args],check=True,capture_output=True,text=True).stdout.strip()

def load_pinned(name, path, expected_blob):
    actual=git('rev-parse',f"{FREEZE['main_commit']}:{path}")
    if actual != expected_blob:
        raise AssertionError({'path':path,'expected':expected_blob,'actual':actual})
    raw=subprocess.run(['git','-C',str(REPO),'show',f"{FREEZE['main_commit']}:{path}"],
                       check=True,capture_output=True).stdout
    module=types.ModuleType(name)
    sys.modules[name]=module
    exec(compile(raw,f"{FREEZE['main_commit']}:{path}",'exec'),module.__dict__)
    return module

clock=load_pinned('independent_progress_clock_v2',
    'research/doom/independent_progress_clock_v2.py',FREEZE['clock_blob'])
ack=load_pinned('acknowledged_scorer_v1',
    'research/doom/acknowledged_scorer_v1.py',FREEZE['acknowledged_scorer_blob'])

class Game:
    def __init__(self, post_update_kills):
        self.tic=1
        self.kills=0
        self.post_update_kills=iter(post_update_kills)
        self.finished=False
    def get_episode_time(self): return self.tic
    def is_episode_finished(self): return self.finished
    def advance_action(self,tics,update_state):
        assert tics==1 and update_state is True
        self.tic+=1
        self.kills=next(self.post_update_kills)

class TickClock:
    def __init__(self): self.values=iter((10,20,40,50))
    def __call__(self): return next(self.values)

def run_world(stale_values):
    # World F samples the live game's counters. World S returns cached values
    # from a previous episode, while the game itself has advanced normally.
    game=Game((0,3) if stale_values else (0,2))
    cached=(0,2)
    sample_counter={'n':0}
    captured=[]
    def sample_fn(current_game, _variables, _timeout):
        sample_index=sample_counter['n']
        sample_counter['n']+=1
        sample_time=(30,60)[sample_index]
        if stale_values:
            kill_count=cached[sample_index]
        else:
            kill_count=current_game.kills
        return clock.ProgressSample(sample_time,kill_count,0,False,False,False)
    sampler=ack.AcknowledgedSampler(sample_fn,'fixed-current-run',captured.append,
                                     clock_ns=TickClock())
    samples=[]
    for _ in range(2): samples.append(sampler(game,None,10))
    progress=clock.ProgressClock()
    events=[]
    for sample in samples: events.extend(progress.ingest(sample))
    return game,samples,captured,events

fresh=run_world(False)
stale=run_world(True)
fresh_game,fresh_samples,fresh_rows,fresh_events=fresh
stale_game,stale_samples,stale_rows,stale_events=stale
checks={
    'different_underlying_current_state': fresh_game.kills==2 and stale_game.kills==3,
    'same_reported_samples': [s.as_dict() for s in fresh_samples]==[s.as_dict() for s in stale_samples],
    'same_client_update_rows': fresh_rows==stale_rows,
    'same_progress_clock_events': fresh_events==stale_events,
    'stale_world_claims_current_update': stale_samples[-1].producer['update_sequence']==2 and
        stale_samples[-1].producer['tic_after']==3 and
        stale_samples[-1].producer['observation_status']=='UPDATE_RETURNED',
    'stale_source_epoch_is_not_present': all('source_epoch' not in row['sample']['producer']
        for row in stale_rows),
}
if not all(checks.values()): raise AssertionError(checks)
result={
  'schema':'v16-source-epoch-probe-a01-result-v1','status':'PASS_COUNTEREXAMPLE',
  'main_commit':FREEZE['main_commit'],'python':platform.python_version(),
  'checks':checks,
  'fresh_current_kills':fresh_game.kills,
  'stale_world_current_kills':stale_game.kills,
  'fresh_reported_samples':[sample.as_dict() for sample in fresh_samples],
  'stale_reported_samples':[sample.as_dict() for sample in stale_samples],
  'fresh_client_update_rows':fresh_rows,
  'stale_client_update_rows':stale_rows,
  'fresh_progress_clock_events':fresh_events,
  'stale_progress_clock_events':stale_events,
  'both_emitted_sample_kills':[s.kill_count for s in stale_samples],
  'wrapper_run_id':stale_samples[-1].producer['run_id'],
  'wrapper_update_sequence':stale_samples[-1].producer['update_sequence'],
  'progress_clock_events':stale_events,
  'interpretation':'V16 records an acknowledged client update and labels the sampled value with that wrapper run, but the accepted sample API contains no identity proving which producer epoch supplied the counters. Identical fresh/stale histories remain indistinguishable.',
  'scope':'Synthetic source-level identifiability construction; does not show the real engine returns stale counters and does not qualify runtime freshness or gameplay.'}
(HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
