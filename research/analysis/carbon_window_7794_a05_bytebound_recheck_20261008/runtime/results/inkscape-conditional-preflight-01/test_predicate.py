import hashlib,json,pathlib,unittest
from PIL import Image
from predicate import classify,retained_cue,LAYOUTS
ROOT=pathlib.Path(__file__).resolve().parent
class PredicateTests(unittest.TestCase):
 def test_all_original_blank_and_drawn_frames(self):
  for row in json.loads((ROOT/'sources.json').read_text())['captures']:
   with self.subTest(file=row['file']): self.assertIs(retained_cue((ROOT/row['file']).read_bytes(),row['sha256'],row['layout']),row['expected'])
 def test_opposite_layout_does_not_admit(self):
  for row in json.loads((ROOT/'sources.json').read_text())['captures']:
   if row['expected']:
    other='diagonal_up' if row['layout']=='diagonal_down' else 'diagonal_down'
    self.assertIsNone(retained_cue((ROOT/row['file']).read_bytes(),row['sha256'],other))
 def test_missing_rectangle_and_uncertain_color_yield_unknown(self):
  row=next(x for x in json.loads((ROOT/'sources.json').read_text())['captures'] if x['expected'])
  with Image.open(ROOT/row['file']) as source: image=source.convert('RGB')
  for color in [(255,255,255),(128,128,128)]:
   changed=image.copy();changed.paste(color,LAYOUTS[row['layout']][0]);self.assertIsNone(classify(changed,row['layout']))
 def test_changed_bytes_and_wrong_frame_rejected(self):
  row=json.loads((ROOT/'sources.json').read_text())['captures'][0];data=(ROOT/row['file']).read_bytes()
  with self.assertRaises(ValueError):retained_cue(data+b'x',row['sha256'],row['layout'])
  self.assertIsNone(classify(Image.new('RGB',(900,600),'white'),row['layout']))
  with self.assertRaises(ValueError):classify(Image.new('RGB',(1000,700),'white'),'undeclared')
if __name__=='__main__':unittest.main()
