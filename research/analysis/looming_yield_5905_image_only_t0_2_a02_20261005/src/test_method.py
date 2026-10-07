import base64,importlib.util,pathlib,unittest
p=pathlib.Path(__file__).with_name('candidate.py');s=importlib.util.spec_from_file_location('cand',p);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
class Construction(unittest.TestCase):
 def test_roundtrip_pgm(self):
  import build_fixture as b
  raw,p=c.pgm(base64.b64encode(b.frame(10)).decode());self.assertEqual(len(p),128*128)
 def test_radius_measurement_monotone(self):
  import build_fixture as b
  a=c.comps(c.pgm(base64.b64encode(b.frame(8)).decode())[1],181,255)[0]['area']
  z=c.comps(c.pgm(base64.b64encode(b.frame(12)).decode())[1],181,255)[0]['area'];self.assertGreater(z,a)
 def test_marker_change_is_in_image(self):
  import build_fixture as b
  a=b.frame(11,marker_scale=1);z=b.frame(11,marker_scale=1.1);self.assertNotEqual(a,z)
if __name__=='__main__':unittest.main(verbosity=2)