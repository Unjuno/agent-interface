import json, runpy, sys, threading, types
from pathlib import Path
script=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(script.parent))
class FakeGame:
    def __init__(self): self.sample_threads=[]; self.initialized=False; self.did_close=False
    def init(self): self.initialized=True; return True
    def close(self): self.did_close=True
    def get_episode_time(self): self.sample_threads.append(threading.get_ident()); return 0
    def is_episode_finished(self): return False
    def is_player_dead(self): return False
    def get_game_variable(self,_): return 0
    def get_ticrate(self): return 35
    def is_episode_timeout_reached(self): return False
base=types.ModuleType('session_map01_v12')
base.vd=types.SimpleNamespace(DoomGame=FakeGame,GameVariable=types.SimpleNamespace(KILLCOUNT='kills',DEATHCOUNT='deaths'))
base.sys=sys

def fake_session_main():
    game=base.vd.DoomGame(); game.init(); polling=sys.stdin
    print(json.dumps({'event':'ready','owner_thread_id':threading.get_ident(),'polling_type':type(polling).__name__}),flush=True)
    try:
        for line in polling:
            parsed_command=json.loads(line)
            print(json.dumps({'event':'command','line':line,'parsed_command':parsed_command,'command_thread_id':threading.get_ident(),
                'polling_owner_thread_id':polling.owner_thread,'periodic_samples':polling.samples,
                'sample_thread_ids':list(game._inner.sample_threads)}),flush=True)
            break
    finally:
        game.close()
base.main=fake_session_main
sys.modules['session_map01_v12']=base
executor=types.ModuleType('executor_v13'); executor.Executor=type('ExecutorStub',(),{})
telemetry=types.ModuleType('doom_owner_thread_release_batch_backend_v1'); telemetry.Backend=type('BackendStub',(),{})
sys.modules['executor_v13']=executor; sys.modules['doom_owner_thread_release_batch_backend_v1']=telemetry
sys.argv=[str(script),*sys.argv[2:]]
runpy.run_path(str(script),run_name='__main__')
