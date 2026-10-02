import pathlib,json,hashlib,unittest
from PIL import Image
from selection_gate import selection_state,BOXES
ROOT=pathlib.Path(__file__).resolve().parent
class GateTests(unittest.TestCase):
 def test_exact_original_frames_and_independent_prior_labels(self):
  rows=json.loads((ROOT/'labels.json').read_text())
  for row in rows:
   p=ROOT/row['file'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256'])
   with Image.open(p) as im:self.assertEqual(selection_state(im.convert('RGB'),row['geometry_state']),row['expected'],row['case'])
 def selected(self):
  row=next(x for x in json.loads((ROOT/'labels.json').read_text()) if x['expected']=='selected');return Image.open(ROOT/row['file']).convert('RGB')
 def test_missing_each_handle_is_unknown(self):
  for box in BOXES:
   im=self.selected();im.paste('white',box);self.assertEqual(selection_state(im,'initial'),'unknown')
 def test_wrong_frame_geometry_or_format_is_unknown(self):
  self.assertEqual(selection_state(Image.new('RGB',(900,600),'white'),'initial'),'unknown')
  self.assertEqual(selection_state(self.selected().convert('L'),'initial'),'unknown')
  self.assertEqual(selection_state(self.selected(),'unknown'),'unknown')
if __name__=='__main__':unittest.main()
