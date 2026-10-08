import unittest
import candidate
import auditor

JOBS = [
    {"id":"A","duration":1,"release":0,"deadline":3,"fresh_until":3,"predecessors":[],"cancelled":False},
    {"id":"B","duration":1,"release":0,"deadline":1,"fresh_until":1,"predecessors":[],"cancelled":False},
]

class Construction(unittest.TestCase):
    def test_global_and_serial_discriminator(self):
        case={"jobs":JOBS}
        jobs, rows=candidate.feasible(case)
        self.assertEqual(min(rows,key=lambda s:tuple(s[j["id"]] for j in jobs)),{"A":1,"B":0})
        self.assertIsNone(candidate.serial_asap(jobs))
    def test_independent_recursive_and_serial_discriminator(self):
        rows=auditor.recursive_assignments(JOBS)
        self.assertEqual(min(rows,key=lambda s:tuple(s[j["id"]] for j in JOBS)),{"A":1,"B":0})
        self.assertIsNone(auditor.independent_serial(JOBS))

if __name__=="__main__": unittest.main()
