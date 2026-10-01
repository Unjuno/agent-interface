import json,unittest,numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from decision import truth,make_payload,extract_validate
class T(unittest.TestCase):
 def test_exhaustive_backends(self):
  X=np.stack([np.array([(m>>i)&1 for i in range(8)],float) for m in range(256)]); y=np.array([truth(x) for x in X])
  l=LogisticRegression(C=1e6,max_iter=10000,solver='lbfgs').fit(X,y); t=DecisionTreeClassifier(random_state=1).fit(X,y)
  self.assertTrue(np.array_equal(l.predict(X),y)); self.assertTrue(np.array_equal(t.predict(X),y))
 def test_extractor(self):
  p=make_payload([1,1,1,1,1,1,1],'LIVE',1); x=extract_validate(p); self.assertEqual(truth(x),0)
  o=json.loads(p); o['request']['authority']='task';
  with self.assertRaises(ValueError): extract_validate(json.dumps(o))
if __name__=='__main__': unittest.main()
