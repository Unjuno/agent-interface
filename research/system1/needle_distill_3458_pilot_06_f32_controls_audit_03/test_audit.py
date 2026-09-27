import struct
import unittest
import audit


class Float32InvalidControlTests(unittest.TestCase):
    def fixtures(self,seed):
        controls=[]
        for case,meta,x,reason in audit.EXPECTED:
            values=[float(v) if v!="NaN" else "NaN" for v in x]
            values=[struct.unpack("f",struct.pack("f",v))[0] if isinstance(v,float) else v for v in values]
            controls.append({"case":case,"meta":meta,"x":values,"reason":reason,"proposal":None})
        return {"seed":seed,"invalid_controls":controls}

    def test_float32_roundtrip_within_tolerance(self):
        errors,count=audit.validate_invalid([self.fixtures(s) for s in audit.prior.SEEDS])
        self.assertEqual(errors,[])
        self.assertEqual(count,15)

    def test_outside_tolerance_is_rejected(self):
        records=[self.fixtures(s) for s in audit.prior.SEEDS]
        records[0]["invalid_controls"][0]["x"][0]+=.001
        errors,_=audit.validate_invalid(records)
        self.assertIn("seed_3467:invalid:stale_epoch:feature_0_mismatch",errors)

    def test_nan_string_encoding_is_exact(self):
        records=[self.fixtures(s) for s in audit.prior.SEEDS]
        records[0]["invalid_controls"][4]["x"][0]=float("nan")
        errors,_=audit.validate_invalid(records)
        self.assertIn("seed_3467:invalid:nonfinite:feature_0_nan_encoding",errors)

    def test_metadata_reason_proposal_and_case_are_exact(self):
        records=[self.fixtures(s) for s in audit.prior.SEEDS]
        records[0]["invalid_controls"][0]["reason"]="PROPOSAL"
        errors,_=audit.validate_invalid(records)
        self.assertIn("seed_3467:invalid:stale_epoch:decision",errors)

    def test_self_test(self):
        audit.self_test()


if __name__=="__main__":
    unittest.main(verbosity=2)
