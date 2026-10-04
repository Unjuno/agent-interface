import ast,time
from pathlib import Path
from independent_progress_clock_v2 import ProgressSample
node=next(n for n in ast.parse(Path('/source/session_map01_v15.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='_coherent_progress_sample')
scope={'ProgressSample':ProgressSample,'time':time};exec(compile(ast.Module(body=[node],type_ignores=[]),'baseline','exec'),scope)
class Game:
 calls=0
 def get_episode_time(self):return 2
 def is_episode_finished(self):return False
 def is_player_dead(self):return False
 def get_game_variable(self,v):return 0
 def get_ticrate(self):return 35
 def advance_action(self,*a):self.calls+=1
class Vars:KILLCOUNT=1;DEATHCOUNT=2
g=Game();scope['_coherent_progress_sample'](g,Vars,10)
assert g.calls==1,'getter-only V15 sampler performed no client update'
