import unittest
import runner
class T(unittest.TestCase):
 def test_construction_shape(self): self.assertEqual(len(runner.execute("construction")),40)
 def test_graph(self): self.assertEqual(runner.graph("UNKNOWN"),"YIELD")
 def test_corrupt_manifest(self): self.assertNotEqual(runner.manifest(1,True,True)["A"],runner.truth(1,"A"))
 def test_incomplete(self): self.assertNotIn("D",runner.manifest(1,False,False))
 def test_schedule_count_without_formal_execution(self): self.assertEqual(len(runner.SCHEDULES),8)
if __name__=="__main__": unittest.main()
