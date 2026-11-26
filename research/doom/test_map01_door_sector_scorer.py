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
if __name__=='__main__':unittest.main()
