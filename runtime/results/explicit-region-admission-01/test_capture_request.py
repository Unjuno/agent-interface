import unittest
from capture_request import region_for
class RegionTests(unittest.TestCase):
 def test_explicit_regions_preserve_origin_and_size(self):
  self.assertEqual(region_for({'capture_region':[0,165,290,116]}),[0,165,290,116])
  self.assertEqual(region_for({}),[0,0,1280,800])
 def test_bad_region_refuses_before_any_call(self):
  for region in ([True,0,1,1],[0,0,0,1],[0,0,1],[0,0,1281,800],[0,790,10,11],[1.0,0,1,1],'auto',None):
   with self.subTest(region=region),self.assertRaises(ValueError):region_for({'capture_region':region})
 def test_returned_list_cannot_mutate_request(self):
  request={'capture_region':[0,165,290,116]};region_for(request)[0]=30
  self.assertEqual(request['capture_region'],[0,165,290,116])
if __name__=='__main__':unittest.main()
