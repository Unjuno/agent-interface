"""Scorer-only last-action observation around unchanged V16 updates.

No game starts on import. Rows never enter controller-visible event delivery.
"""
from pathlib import Path
import sys,json,time,os
source=Path('/study/sample-pair-source-02')
for name in ['doom','live_control','real_apps_v1','observation_gating','observation_tiles']:
    sys.path.insert(0,str(source/'research'/name))
import vizdoom as vd
import session_map01_v16 as session

class ScorerOnlyActionProxy:
    def __init__(self,inner): self.inner=inner
    def __getattr__(self,name): return getattr(self.inner,name)
    def advance_action(self,*args,**kwargs):
        returned=self.inner.advance_action(*args,**kwargs)
        begin=time.perf_counter_ns()
        tic_before=self.inner.get_episode_time()
        action=list(self.inner.get_last_action())
        tic_after=self.inner.get_episode_time()
        end=time.perf_counter_ns()
        row={'event':'scorer_last_action','sample_started_ns':begin,'sample_returned_ns':end,
             'tic_before':tic_before,'tic_after':tic_after,'buttons':[str(x) for x in self.inner.get_available_buttons()],
             'action':action,'coherent_tic':tic_before==tic_after,
             'authority':False,'scope':'sampled last-action API; exact transition onset unproven'}
        with Path(os.environ['ACTION_SAMPLE_PATH']).open('a') as stream:
            stream.write(json.dumps(row)+'\n')
        return returned

if __name__=='__main__':
    original=vd.DoomGame
    vd.DoomGame=lambda:ScorerOnlyActionProxy(original())
    try: session.main()
    finally: vd.DoomGame=original
