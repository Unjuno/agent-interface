import unittest
import torch
import audit


class Pilot07AuditLogicTests(unittest.TestCase):
    def test_original_quality_gate_pass_and_fail(self):
        rows=[]
        for label,name in enumerate(audit.LABELS):
            rows.extend([{"y":label,"proposal":name} for _ in range(1024)])
        self.assertTrue(audit.quality_gate(audit.summarize(rows)))
        for row in rows[1024:1124]: row["proposal"]="CONTINUE"
        self.assertFalse(audit.quality_gate(audit.summarize(rows)))

    def test_near_boundary_contract_checks_all_six_columns(self):
        good=[.1,.0,.01,-.01,.9,1.]
        self.assertTrue(audit.near_bounds(good))
        for col,bad in ((0,.16),(1,.11),(2,.06),(3,-.06),(4,.79),(5,0.)):
            row=good.copy(); row[col]=bad
            self.assertFalse(audit.near_bounds(row),col)

    def test_six_feature_generators_are_seeded_and_suite_specific(self):
        a=audit.shifted_class(1,8,4010).tolist()
        b=audit.shifted_class(1,8,4010).tolist()
        self.assertEqual(a,b)
        iid=audit.balanced_class(1,8,4010).tolist()
        self.assertNotEqual(iid[0][2:5],a[0][2:5])

    def test_teacher_and_fail_closed_reasons(self):
        self.assertEqual(audit.teacher([[0,0,0,0,.9,1],[.2,.2,0,0,.9,1],[0,0,0,0,.2,0]]),[0,1,2])
        self.assertEqual(audit.reason(audit.META,[.2,.2,0,0,.9,1]),"PROPOSAL")
        self.assertEqual(audit.reason({"epoch":8},[.2,.2,0,0,.9,1]),"YIELD_METADATA")

    def test_dataset_sizes_and_seed_count_fixed(self):
        self.assertEqual(audit.SEEDS,(3480,3481,3482))
        self.assertEqual(len(audit.boundary_rows()),1536)
        self.assertEqual(len(audit.invalid_expected()),5)

    def test_training_rows_and_batch_digest_reconstruct(self):
        control,_=audit.training_rows_expected(3480,False)
        treatment,_=audit.training_rows_expected(3480,True)
        self.assertTrue(torch.equal(control[:2048],treatment[:2048]))
        self.assertTrue(torch.equal(control[4096:],treatment[4096:]))
        self.assertNotEqual(audit.expected_batch_hash(3480),audit.expected_batch_hash(3481))


if __name__=="__main__": unittest.main(verbosity=2)
