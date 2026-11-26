import tempfile,unittest
from pathlib import Path
from map01_door_sector_scorer import DoorSectorScorer

class Line:
 def __init__(self,x1,y1,x2,y2):self.x1=x1;self.y1=y1;self.x2=x2;self.y2=y2
class Sector:
 def __init__(self,floor=64,ceiling=-64):
  self.floor_height=floor;self.ceiling_height=ceiling
  self.lines=[Line(704,-96,704,-224),Line(720,-96,720,-224)]
class State:
 def __init__(self,sectors,tic,number):self.sectors=sectors;self.tic=tic;self.number=number
class Game:
 def __init__(self):self.tic=870;self.sectors=[Sector()];self.refreshes=0;self.action=[0.0]*9
 def get_last_action(self):return self.action
 def get_episode_time(self):return self.tic
 def advance_action(self,n,update):
  assert n==1 and update is True
  self.refreshes+=1;self.tic+=1
 def get_state(self):return State(self.sectors,self.tic,self.refreshes)

class SectorScorerTests(unittest.TestCase):
 def test_ordered_neutral_samples_stay_out_of_return_value(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'sector.jsonl';scorer=DoorSectorScorer(path,clock=lambda:1_100_000_000)
   game=Game()
   self.assertIsNone(scorer.sample('cover-0',game,1_000_000_000,lambda:True))
   self.assertEqual(game.refreshes,1)
   row=__import__('json').loads(path.read_text());self.assertEqual(row['gap'],0)
   with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
 def test_traversal_records_private_same_state_position_and_extra_stage(self):
  import inspect,json
  self.assertIn('traverse',inspect.signature(DoorSectorScorer).parameters)
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'private';game=Game()
   def state():
    result=State(game.sectors,game.tic,game.refreshes);result.game_variables=[0,0,687.9,-192,0,100];return result
   game.get_state=state
   scorer=DoorSectorScorer(path,clock=lambda:1_100_000_000,traverse=True)
   for stage in ('cover-0','approach-1','approach-2','approach-3','approach-4','intervention','traverse-1'):
    self.assertIsNone(scorer.sample(stage,game,1_000_000_000,lambda:True))
   rows=[json.loads(line) for line in path.read_text().splitlines()]
   self.assertEqual(rows[-1]['position_x'],687.9);self.assertEqual(rows[-1]['position_y'],-192)
   self.assertEqual(rows[-1]['health'],100);self.assertEqual(rows[-1]['death_count'],0)
 def test_traverse_holds_when_same_state_position_is_missing_or_nonfinite(self):
  import json
  for values in (None,[0,0,float('nan'),-192,0,100],[0,0,1]):
   with self.subTest(values=values),tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'private';game=Game()
    def state():
     result=State(game.sectors,game.tic,game.refreshes);result.game_variables=values;return result
    game.get_state=state;scorer=DoorSectorScorer(path,clock=lambda:1_100_000_000,traverse=True)
    with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
    self.assertEqual(json.loads(path.read_text())['status'],'HOLD')
 def test_final_finished_sample_requires_neutral_without_advancing(self):
  import inspect,json
  self.assertIn('exit_probe',inspect.signature(DoorSectorScorer).parameters)
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'private';game=Game()
   def state():
    result=State(game.sectors,game.tic,game.refreshes);result.game_variables=[0,0,687.9,-192,0,100];return result
   game.get_state=state;game.is_episode_finished=lambda:False
   scorer=DoorSectorScorer(path,clock=lambda:1_100_000_000,traverse=True,exit_probe=True)
   for stage in ('cover-0','approach-1','approach-2','approach-3','approach-4','intervention','traverse-1'):
    scorer.sample(stage,game,1_000_000_000,lambda:True)
   before=game.refreshes
   game.is_episode_finished=lambda:True;game.is_player_dead=lambda:False
   game.is_episode_timeout_reached=lambda:False
   game.get_game_variable=lambda variable:0.0
   scorer.sample('exit-probe',game,1_000_000_000,lambda:True)
   self.assertEqual(game.refreshes,before)
   row=json.loads(path.read_text().splitlines()[-1]);self.assertEqual(row['status'],'terminal_probe_observed')
   self.assertTrue(row['episode_finished']);self.assertFalse(row['native_timeout']);self.assertEqual(row['death_count'],0)
 def test_final_unfinished_sample_is_passive_too(self):
  import json
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'private';game=Game()
   def state():
    result=State(game.sectors,game.tic,game.refreshes);result.game_variables=[0,0,687.9,-192,0,100];return result
   game.get_state=state;game.is_episode_finished=lambda:False
   scorer=DoorSectorScorer(path,clock=lambda:1_100_000_000,traverse=True,exit_probe=True)
   for stage in ('cover-0','approach-1','approach-2','approach-3','approach-4','intervention','traverse-1'):
    scorer.sample(stage,game,1_000_000_000,lambda:True)
   game.is_player_dead=lambda:False;game.is_episode_timeout_reached=lambda:False
   game.get_game_variable=lambda variable:0.0
   before=game.refreshes;scorer.sample('exit-probe',game,1_000_000_000,lambda:True)
   self.assertEqual(game.refreshes,before)
   row=json.loads(path.read_text().splitlines()[-1]);self.assertFalse(row['episode_finished'])
   self.assertEqual(row['refresh_count'],0)
 def test_final_neutral_check_must_finish_before_deadline(self):
  import json
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'private';game=Game();now=[1_100_000_000]
   def state():
    result=State(game.sectors,game.tic,game.refreshes);result.game_variables=[0,0,687.9,-192,0,100];return result
   game.get_state=state;game.is_episode_finished=lambda:False
   scorer=DoorSectorScorer(path,clock=lambda:now[0],traverse=True,exit_probe=True)
   for stage in ('cover-0','approach-1','approach-2','approach-3','approach-4','intervention','traverse-1'):
    scorer.sample(stage,game,1_000_000_000,lambda:True)
   game.is_player_dead=lambda:False;game.is_episode_timeout_reached=lambda:False;game.get_game_variable=lambda variable:0.0
   calls=[]
   def neutral():
    calls.append(True)
    if len(calls)==2:now[0]=2_010_000_000
    return True
   with self.assertRaises(ValueError):scorer.sample('exit-probe',game,1_000_000_000,neutral)
   self.assertEqual(json.loads(path.read_text().splitlines()[-1])['status'],'HOLD')
 def test_final_probe_rejects_mixed_engine_tics(self):
  import json
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'private';game=Game()
   def state():
    result=State(game.sectors,game.tic,game.refreshes);result.game_variables=[0,0,687.9,-192,0,100];return result
   game.get_state=state;game.is_episode_finished=lambda:False
   scorer=DoorSectorScorer(path,clock=lambda:1_100_000_000,traverse=True,exit_probe=True)
   for stage in ('cover-0','approach-1','approach-2','approach-3','approach-4','intervention','traverse-1'):
    scorer.sample(stage,game,1_000_000_000,lambda:True)
   ticks=iter((100,101));game.get_episode_time=lambda:next(ticks)
   game.is_player_dead=lambda:False;game.is_episode_timeout_reached=lambda:False;game.get_game_variable=lambda variable:0.0
   with self.assertRaises(ValueError):scorer.sample('exit-probe',game,1_000_000_000,lambda:True)
   self.assertEqual(json.loads(path.read_text().splitlines()[-1])['status'],'HOLD')
 def test_final_terminal_unknown_timeout_or_non_neutral_is_hold(self):
  import json
  for condition in ('timeout','neutral'):
   with self.subTest(condition=condition),tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'private';game=Game()
    def state():
     result=State(game.sectors,game.tic,game.refreshes);result.game_variables=[0,0,687.9,-192,0,100];return result
    game.get_state=state;game.is_episode_finished=lambda:False
    scorer=DoorSectorScorer(path,clock=lambda:1_100_000_000,traverse=True,exit_probe=True)
    for stage in ('cover-0','approach-1','approach-2','approach-3','approach-4','intervention','traverse-1'):
     scorer.sample(stage,game,1_000_000_000,lambda:True)
    game.is_episode_finished=lambda:True;game.is_player_dead=lambda:False
    game.is_episode_timeout_reached=lambda:None if condition=='timeout' else False
    game.get_game_variable=lambda variable:0.0
    before=game.refreshes
    with self.assertRaises(ValueError):scorer.sample('exit-probe',game,1_000_000_000,lambda:condition!='neutral')
    self.assertEqual(game.refreshes,before)
    self.assertEqual(json.loads(path.read_text().splitlines()[-1])['status'],'HOLD')
 def test_stale_state_and_physical_input_are_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   game=Game();scorer=DoorSectorScorer(Path(temp)/'stale',clock=lambda:1_100_000_000)
   game.get_state=lambda:State(game.sectors,870,1)
   with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
   game=Game();scorer=DoorSectorScorer(Path(temp)/'keys',clock=lambda:1_100_000_000)
   with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:False)
   row=__import__('json').loads((Path(temp)/'keys').read_text())
   self.assertFalse(row['refresh_attempted'])
 def test_refresh_is_not_accepted_after_terminal_sampling_window(self):
  with tempfile.TemporaryDirectory() as temp:
   values=iter((1_950_000_000,2_010_000_000))
   game=Game();scorer=DoorSectorScorer(Path(temp)/'late-before',clock=lambda:next(values))
   with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
   row=__import__('json').loads((Path(temp)/'late-before').read_text())
   self.assertFalse(row['refresh_attempted'])
   values=iter((1_900_000_000,1_950_000_000,2_010_000_000))
   game=Game();scorer=DoorSectorScorer(Path(temp)/'late-after',clock=lambda:next(values))
   with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
   row=__import__('json').loads((Path(temp)/'late-after').read_text())
   self.assertTrue(row['refresh_attempted']);self.assertTrue(row['refresh_returned'])
 def test_ambiguous_or_non_neutral_state_is_not_scored(self):
  with tempfile.TemporaryDirectory() as temp:
   for bad in ('two','keys','missing'):
    with self.subTest(bad=bad):
     game=Game();scorer=DoorSectorScorer(Path(temp)/(bad+'.jsonl'),clock=lambda:1_100_000_000)
     if bad=='two':game.sectors.append(Sector())
     if bad=='missing':game.sectors=[]
     if bad=='keys':game.action[7]=1
     with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
class ReverseScorerConfigurationTests(unittest.TestCase):
 def test_reverse_stages_are_explicitly_opt_in(self):
  from map01_reverse_program import reverse_stages
  with tempfile.TemporaryDirectory() as temp:
   scorer=DoorSectorScorer(Path(temp)/'private.jsonl',traverse=True,reverse_arm='use')
   self.assertEqual(scorer.STAGES[-len(reverse_stages('use')):],tuple(x[0] for x in reverse_stages('use')))
   with self.assertRaises(ValueError):DoorSectorScorer(Path(temp)/'bad.jsonl',reverse_arm='use')
   with self.assertRaises(ValueError):DoorSectorScorer(Path(temp)/'bad2.jsonl',traverse=True,exit_probe=True,reverse_arm='use')
if __name__=='__main__':unittest.main()
