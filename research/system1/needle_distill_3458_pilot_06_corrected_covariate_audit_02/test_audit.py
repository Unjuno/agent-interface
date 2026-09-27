import unittest
import audit


class CorrectedCovariateAuditTests(unittest.TestCase):
    def test_each_feature_column_is_independently_bound(self):
        row=[.1,.02,-.03,.01,.9,1.]
        for col in range(6):
            with self.subTest(column=col):
                changed=row.copy(); changed[col]+=.01
                self.assertEqual(audit.vector_errors(changed,row),[f"feature_{col}_mismatch"])

    def test_suite_specific_velocity_confidence_may_differ(self):
        iid=audit.balanced(1,4,123).tolist()
        shifted=audit.shifted(1,4,123).tolist()
        self.assertNotEqual(iid[0][2:5],shifted[0][2:5])
        self.assertEqual(audit.vector_errors(shifted[0],audit.shifted(1,4,123).tolist()[0]),[])

    def test_shift_bounds_include_confidence_and_visibility(self):
        rows=audit.shifted(1,1024,3568).tolist()
        for dx,dy,vx,vy,confidence,visible in rows:
            self.assertTrue(.071-1e-6<=abs(dx)<=.149+1e-6)
            self.assertLessEqual(abs(dy),.10+1e-6)
            self.assertLessEqual(abs(vx),.05+1e-6)
            self.assertLessEqual(abs(vy),.05+1e-6)
            self.assertTrue(.80-1e-6<=confidence<=1+1e-6)
            self.assertEqual(visible,1.)

    def test_wrong_width_and_nonfinite_fail_closed(self):
        self.assertEqual(audit.vector_errors([.1]*5,[.1]*6),["feature_width"])
        self.assertIn("feature_4_mismatch",audit.vector_errors([.1,.02,-.03,.01,float("nan"),1.],[.1,.02,-.03,.01,.9,1.]))

    def test_six_feature_corruption_controls(self):
        audit.self_test()

    def test_generator_deterministic(self):
        self.assertEqual(audit.shifted(1,16,789).tolist(),audit.shifted(1,16,789).tolist())


if __name__=="__main__":
    unittest.main(verbosity=2)
