import unittest
from PIL import Image
from methods import cue
class CueTests(unittest.TestCase):
 def test_initial_moved_unknown_and_wrong_frame(self):
  initial=Image.new('RGB',(1000,700),'white');initial.paste('red',(340,300,350,315));self.assertEqual(cue(initial),'initial')
  moved=Image.new('RGB',(1000,700),'white');moved.paste('red',(399,300,404,315));self.assertEqual(cue(moved),'moved')
  for im in [Image.new('RGB',(1000,700),'white'),Image.new('RGB',(900,600),'white')]:self.assertEqual(cue(im),'unknown')
 def test_missing_or_ambiguous_pixels_do_not_admit(self):
  im=Image.new('RGB',(1000,700),'white');im.paste('red',(399,300,404,315));im.paste('red',(340,300,350,315));self.assertEqual(cue(im),'unknown')
  im.paste('gray',(340,300,350,315));self.assertEqual(cue(im),'unknown')
if __name__=='__main__':unittest.main()
