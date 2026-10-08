import unittest
from geometry_guard import authorize
class GeometryGuardTests(unittest.TestCase):
 def setUp(self):self.g=dict(window_id=17,x=0,y=19,width=1280,height=781,map_state=2)
 def test_same(self):self.assertEqual(authorize(self.g,[dict(self.g)]),'ACCEPT')
 def test_physical_change(self):self.assertEqual(authorize(self.g,[dict(self.g,x=80)]),'STALE_GEOMETRY')
 def test_missing(self):self.assertEqual(authorize(self.g,[]),'NO_MATCH')
 def test_ambiguity(self):self.assertEqual(authorize(self.g,[self.g,self.g]),'AMBIGUOUS')
 def test_unavailable(self):self.assertEqual(authorize(self.g,None),'UNAVAILABLE')
 def test_new_target(self):self.assertEqual(authorize(self.g,[dict(self.g,window_id=18)]),'STALE_GEOMETRY')
 def test_unmapped(self):self.assertEqual(authorize(self.g,[dict(self.g,map_state=0)]),'UNAVAILABLE')
 def test_missing_field(self):self.assertEqual(authorize(self.g,[{'window_id':17}]),'UNAVAILABLE')
if __name__=='__main__':unittest.main()
