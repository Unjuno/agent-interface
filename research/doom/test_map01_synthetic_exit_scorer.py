import tempfile,unittest
from pathlib import Path
import vizdoom as vd
import importlib.util
class State:
 def __init__(self,tic): self.tic=tic
class Game:
 def __init__(self):self.tic=101;self.x=80;self.finished=False;self.refreshes=0;self.action=[0.0]*9
 def advance_action(self,n,update):self.refreshes+=1;self.tic+=1
 def get_episode_time(self):return self.tic
 def get_state(self):return None if self.finished else State(self.tic)
 def get_last_action(self):return self.action
 def is_episode_finished(self):return self.finished
 def is_player_dead(self):return False
 def is_episode_timeout_reached(self):return False
 def get_game_variable(self,v):
  return {vd.GameVariable.POSITION_X:self.x,vd.GameVariable.POSITION_Y:0.0,
          vd.GameVariable.ANGLE:0.0,vd.GameVariable.HEALTH:100.0,
          vd.GameVariable.DEATHCOUNT:0.0}[v]
class Tests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('map01_synthetic_exit_scorer'))
  global SyntheticExitScorer
  from map01_synthetic_exit_scorer import SyntheticExitScorer
 def test_exact_initial_state_then_terminal_without_refresh(self):
  import json
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'score.jsonl';scorer=SyntheticExitScorer(path,clock=lambda:1_100_000_000);game=Game()
   scorer.sample('cover-0',game,1_000_000_000,lambda:True)
   self.assertEqual(game.refreshes,1)
   game.finished=True;game.tic=0
   scorer.sample('exit-probe',game,1_000_000_000,lambda:True)
   rows=[json.loads(line) for line in path.read_text().splitlines()]
   self.assertEqual([row['stage'] for row in rows],['cover-0','exit-probe'])
   self.assertTrue(rows[-1]['episode_finished']);self.assertEqual(rows[-1]['refresh_count'],0)
 def test_terminal_engine_action_is_recorded_separately_from_physical_release(self):
  import json
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'score';scorer=SyntheticExitScorer(path,clock=lambda:1_100_000_000);game=Game()
   scorer.sample('cover-0',game,1_000_000_000,lambda:True)
   game.finished=True;game.tic=0;game.action=[0.0]*7+[1.0]+[0.0]
   scorer.sample('exit-probe',game,1_000_000_000,lambda:True)
   row=json.loads(path.read_text().splitlines()[-1])
   self.assertEqual(row['engine_last_action'],game.action)
   self.assertTrue(row['physical_neutral_before_after'])
   self.assertEqual(row['refresh_count'],0)
 def test_expired_refresh_does_not_advance_and_failure_records_attempt_state(self):
  import json
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'score';clock=iter((1_100_000_000,2_010_000_000));scorer=SyntheticExitScorer(path,clock=lambda:next(clock));game=Game()
   with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
   row=json.loads(path.read_text());self.assertFalse(row['refresh_attempted']);self.assertFalse(row['refresh_returned'])
   self.assertEqual(game.refreshes,0)
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'score';scorer=SyntheticExitScorer(path,clock=lambda:1_100_000_000);game=Game()
   def fail(n,update):raise RuntimeError('refresh failed')
   game.advance_action=fail
   with self.assertRaises(RuntimeError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
   row=json.loads(path.read_text());self.assertTrue(row['refresh_attempted']);self.assertFalse(row['refresh_returned'])
   self.assertTrue(path.with_name(path.name+'.refresh.jsonl').exists())
 def test_slow_attempt_log_never_advances_after_deadline(self):
  import json
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'score';now=[1_100_000_000];scorer=SyntheticExitScorer(path,clock=lambda:now[0]);game=Game()
   original=scorer._refresh_record
   def slow(row):
    original(row)
    if row['event']=='attempt':now[0]=2_010_000_000
   scorer._refresh_record=slow
   with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
   self.assertEqual(game.refreshes,0)
   row=json.loads(path.read_text());self.assertFalse(row['refresh_attempted'])
   logs=[json.loads(line) for line in path.with_name(path.name+'.refresh.jsonl').read_text().splitlines()]
   self.assertEqual([entry['event'] for entry in logs],['attempt','expired_before_call'])
 def test_changed_spawn_is_hold_and_blocks_next_stage(self):
  with tempfile.TemporaryDirectory() as temp:
   scorer=SyntheticExitScorer(Path(temp)/'score',clock=lambda:1_100_000_000);game=Game();game.x=81
   with self.assertRaises(ValueError):scorer.sample('cover-0',game,1_000_000_000,lambda:True)
   with self.assertRaises(ValueError):scorer.sample('exit-probe',game,1_000_000_000,lambda:True)
if __name__=='__main__':unittest.main()
