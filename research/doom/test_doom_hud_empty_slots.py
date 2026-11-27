import pathlib,os,tempfile,unittest
import numpy as np
from PIL import Image
from doom_hud_signal_v3 import DoomStatusNumberReader
from doom_hud_signal_v1 import _wad_lumps,_render_patch,FREEDOOM2_SHA256

WAD=pathlib.Path(os.environ.get('AI_TEST_WAD', str(pathlib.Path(__file__).resolve().parents[2] / '_vizdoom/vizdoom/freedoom2.wad')))
class EmptySlotRegression(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.reader=DoomStatusNumberReader(WAD,signal_id='health');lumps=_wad_lumps(WAD,FREEDOOM2_SHA256);palette=np.frombuffer(lumps['PLAYPAL'][:768],dtype=np.uint8).reshape(256,3);cls.bar=np.asarray(Image.fromarray(_render_patch(lumps['STBAR'],palette)).convert('RGB').resize((640,76),Image.Resampling.NEAREST));cls.obs={'sequence':1,'capture_ns':1,'pointer_binding':{'focus':7,'surface':7,'geometry':[0,0,640,480]}}
 def image(self,value):
  a=np.zeros((480,640,3),dtype=np.uint8);a[404:480,:]=self.bar
  digits=str(value);w,h=self.reader.glyph_size;left,top=self.reader.local_anchor
  for i,c in enumerate(digits):
   slot=3-len(digits)+i;template,mask=self.reader.templates[int(c)];sub=a[top:top+h,left+slot*w:left+(slot+1)*w];sub[mask]=template[mask]
  return a
 def test_partial_leading_glyph_cannot_be_accepted_as_empty(self):
  a=self.image(100);left,top=self.reader.local_anchor;a[top:top+38,left+12:left+15]=0
  self.assertEqual(self.reader.read_frame(self.obs,Image.fromarray(a))['status'],'unknown')
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'frame.png';Image.fromarray(a).save(p);self.assertEqual(self.reader.read({**self.obs,'image':str(p)})['status'],'unknown')
 def test_clean_zero_through_199_still_read(self):
  for n in range(200):
   with self.subTest(value=n):self.assertEqual(self.reader.read_frame(self.obs,Image.fromarray(self.image(n)))['value'],n)
 def test_frame_and_file_paths_agree_for_clean_and_obscured(self):
  with tempfile.TemporaryDirectory() as tmp:
   for n in (0,9,84,97,100,199):
    for obscured in (False,True):
     a=self.image(n)
     if obscured:
      left,top=self.reader.local_anchor;a[top:top+38,left+12:left+15]=0
     p=pathlib.Path(tmp)/f'{n}-{obscured}.png';Image.fromarray(a).save(p);obs={**self.obs,'image':str(p)};self.assertEqual(self.reader.read_frame(obs,Image.fromarray(a)),self.reader.read(obs))
 def test_occluded_values_never_change_to_different_observed_value(self):
  left,top=self.reader.local_anchor
  for n in (84,90,97,100):
   for width in (3,6,12):
    for start in range(0,78,6):
     with self.subTest(value=n,width=width,start=start):
      a=self.image(n);a[top:top+38,left+start:left+min(start+width,78)]=0
      result=self.reader.read_frame(self.obs,Image.fromarray(a))
      self.assertTrue(result['status']=='unknown' or result['value']==n)
 def test_ammo_values_and_partial_leading_glyph(self):
  original=self.reader;self.reader=DoomStatusNumberReader(WAD,signal_id='ammo')
  try:
   for n in (0,1,9,10,48,100,199):
    with self.subTest(value=n):self.assertEqual(self.reader.read_frame(self.obs,Image.fromarray(self.image(n)))['value'],n)
   a=self.image(100);left,top=self.reader.local_anchor;a[top:top+38,left+12:left+15]=0
   self.assertEqual(self.reader.read_frame(self.obs,Image.fromarray(a))['status'],'unknown')
  finally:self.reader=original
if __name__=='__main__':unittest.main()
