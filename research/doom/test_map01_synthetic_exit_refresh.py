import importlib.util,json,tempfile,unittest
from pathlib import Path
import vizdoom as vd
class Fake:
 def __init__(self):self.tic=100;self.finished=False;self.calls=0;self.action=[0.0]*9
 def get_episode_time(self):return self.tic
 def is_episode_finished(self):return self.finished
 def is_player_dead(self):return False
 def is_episode_timeout_reached(self):return False
 def get_game_variable(self,variable):return 0.0
 def get_last_action(self):return self.action
 def advance_action(self,n,update):self.calls+=1;self.finished=True;self.tic=0
class Tests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('map01_synthetic_exit_refresh'))
  global synchronize_terminal
  from map01_synthetic_exit_refresh import synchronize_terminal
 def test_one_neutral_refresh_records_reset_and_finished(self):
  with tempfile.TemporaryDirectory() as temp:
   game=Fake();out=Path(temp);result=synchronize_terminal(game,out,lambda:True,lambda:{'verified':True},deadline_ns=2_000_000_000,clock=lambda:1_100_000_000)
   self.assertEqual(game.calls,1);self.assertFalse(result['before']['finished']);self.assertTrue(result['after']['finished'])
   self.assertEqual(result['before']['tic'],100);self.assertEqual(result['after']['tic'],0)
   rows=[json.loads(line) for line in (out/'synthetic-terminal-refresh.jsonl').read_text().splitlines()]
   self.assertEqual([r['event'] for r in rows],['before','attempt','pre_call','returned','after'])
 def test_unverified_neutral_or_expired_deadline_never_calls(self):
  for neutral,deadline in ((False,2_000_000_000),(True,1_000_000_000)):
   with self.subTest(neutral=neutral,deadline=deadline),tempfile.TemporaryDirectory() as temp:
    game=Fake()
    with self.assertRaises(ValueError):synchronize_terminal(game,Path(temp),lambda:neutral,lambda:{'verified':True},deadline_ns=deadline,clock=lambda:1_100_000_000)
    self.assertEqual(game.calls,0)
 def test_late_return_is_recorded_and_never_retried(self):
  with tempfile.TemporaryDirectory() as temp:
   game=Fake(); now=[1_100_000_000]
   def advance(n,update):
    game.calls+=1;game.finished=True;game.tic=0;now[0]=2_100_000_000
   game.advance_action=advance
   with self.assertRaises(ValueError):synchronize_terminal(game,Path(temp),lambda:True,lambda:{'verified':True},deadline_ns=2_000_000_000,clock=lambda:now[0])
   self.assertEqual(game.calls,1)
   rows=[json.loads(line) for line in (Path(temp)/'synthetic-terminal-refresh.jsonl').read_text().splitlines()]
   self.assertEqual([r['event'] for r in rows],['before','attempt','pre_call','returned','after','error'])
   self.assertTrue(rows[4]['sample']['finished'])
 def test_finished_with_death_count_or_late_sample_is_not_early_success(self):
  for death,late in ((1,False),(0,True)):
   with self.subTest(death=death,late=late),tempfile.TemporaryDirectory() as temp:
    game=Fake();game.finished=True;game.get_game_variable=lambda variable: float(death)
    calls=[0]
    def clock():
     calls[0]+=1
     return 2_100_000_000 if late and calls[0]>=3 else 1_100_000_000
    with self.assertRaises(ValueError):synchronize_terminal(game,Path(temp),lambda:True,lambda:{'verified':True},deadline_ns=2_000_000_000,clock=clock)
    self.assertEqual(game.calls,0)
    rows=[json.loads(line) for line in (Path(temp)/'synthetic-terminal-refresh.jsonl').read_text().splitlines()]
    self.assertEqual([r['event'] for r in rows],['before'])
 def test_existing_finished_with_frozen_use_is_preserved_without_call(self):
  with tempfile.TemporaryDirectory() as temp:
   game=Fake();game.finished=True;game.action[0]=1.0
   result=synchronize_terminal(game,Path(temp),lambda:True,lambda:{'verified':True},deadline_ns=2_000_000_000,clock=lambda:1_100_000_000)
   self.assertEqual(game.calls,0);self.assertEqual(result['before']['last_action'][0],1.0)
 def test_natural_finish_between_samples_skips_synchronization(self):
  with tempfile.TemporaryDirectory() as temp:
   game=Fake(); reads=[False,True]
   game.is_episode_finished=lambda:reads.pop(0)
   result=synchronize_terminal(game,Path(temp),lambda:True,lambda:{'verified':True},deadline_ns=2_000_000_000,clock=lambda:1_100_000_000)
   self.assertEqual(game.calls,0);self.assertEqual(result['disposition'],'already_finished')
   rows=[json.loads(line) for line in (Path(temp)/'synthetic-terminal-refresh.jsonl').read_text().splitlines()]
   self.assertEqual([r['event'] for r in rows],['before','attempt','pre_call','already_finished_before_call'])
 def test_non_neutral_engine_action_does_not_advance(self):
  with tempfile.TemporaryDirectory() as temp:
   game=Fake();game.action[0]=1.0
   with self.assertRaises(ValueError):synchronize_terminal(game,Path(temp),lambda:True,lambda:{'verified':True},deadline_ns=2_000_000_000,clock=lambda:1_100_000_000)
   self.assertEqual(game.calls,0)
 def test_already_finished_does_not_advance(self):
  with tempfile.TemporaryDirectory() as temp:
   game=Fake();game.finished=True;game.tic=0
   result=synchronize_terminal(game,Path(temp),lambda:True,lambda:{'verified':True},deadline_ns=2_000_000_000,clock=lambda:1_100_000_000)
   self.assertEqual(game.calls,0);self.assertEqual(result['disposition'],'already_finished')
if __name__=='__main__':unittest.main()
