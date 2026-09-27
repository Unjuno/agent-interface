import unittest
import experiment as e

class StudyTests(unittest.TestCase):
    def test_control_labels(self):
        rows=e.controls()
        self.assertEqual([e.oracle(x) for x in rows],[3,4,3,5])
        self.assertEqual([e.rule(x) for x in rows],[3,4,3,5])
        self.assertLess(rows[2][4],.28)
    def test_deterministic_data_and_split(self):
        a=e.dataset(8304391,32); b=e.dataset(8304391,32)
        self.assertEqual(a,b)
        self.assertNotEqual(e.dataset(8304391,8)[0],e.dataset(8404391,8,True)[0])
    def test_tree_fit(self):
        x,y=e.dataset(8304391,128)
        t=e.fit_tree(x,y)
        self.assertTrue(all(0<=e.tree_predict(t,row)<6 for row in x))

    def test_mlp_shape_and_train(self):
        x,y=e.dataset(8304391,16)
        state=e.fit_mlp(x,y,8304422)
        self.assertEqual(len(x[0]),12)
        self.assertEqual(len(state["0.weight"]),16)
        self.assertTrue(all(0<=e.mlp_predict(state,row)<6 for row in x))

if __name__=="__main__":unittest.main()
