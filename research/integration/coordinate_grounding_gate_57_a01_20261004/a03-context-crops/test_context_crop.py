from __future__ import annotations
import unittest
from candidate import run_experiment


class ContextCropTargetHandleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=run_experiment()

    def test_context_padding_recovers_all_five_field_handles(self):
        summary=self.result["summary"]
        self.assertEqual(summary["padded_crop_valid"],5)
        for case in self.result["cases"]:
            self.assertEqual(case["padded_crop"]["status"],"VALID",case["task"])
            self.assertEqual(case["padded_crop"]["resolved_point"],case["field_point"])
            self.assertLessEqual(max(case["padded_crop"]["box"][2:]),96)

    def test_raw_model_crops_remain_flat_and_refuse(self):
        self.assertEqual(self.result["summary"]["raw_crop_valid"],0)
        self.assertEqual(self.result["summary"]["raw_crop_flat_refused"],5)
        self.assertTrue(all(case["raw_crop"]["registry_entries"]==0 for case in self.result["cases"]))

    def test_changed_padded_region_refuses_all_five_handles(self):
        self.assertEqual(self.result["summary"]["padded_crop_changed_missing"],5)
        self.assertTrue(all(case["padded_crop_after_region_replacement"]["status"]=="MISSING" and
                            case["padded_crop_after_region_replacement"]["eligible"] is False
                            for case in self.result["cases"]))
        self.assertEqual(self.result["summary"]["input_dispatch_count"],0)


if __name__=="__main__": unittest.main(verbosity=2)
