import copy
import json
import pathlib
import tempfile
import unittest

import auditor
import candidate


ROOT=pathlib.Path(__file__).parent
FIXTURE=ROOT/"fixture.json"


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.raw=pathlib.Path(self.tmp.name)/"raw.json"
        candidate.main(str(FIXTURE),str(self.raw),construction=True)
        self.fixture=json.loads(FIXTURE.read_text())
        self.data=json.loads(self.raw.read_text())

    def tearDown(self):
        self.tmp.cleanup()

    def audit_data(self,data):
        path=pathlib.Path(self.tmp.name)/"mutated.json"
        path.write_text(json.dumps(data))
        return auditor.audit(str(FIXTURE),str(path),construction=True)

    def test_construction_replays_all_rows(self):
        result=auditor.audit(str(FIXTURE),str(self.raw),construction=True)
        self.assertEqual(result["rows"],36)
        self.assertEqual(result["errors"],[])

    def test_formal_seeds_disjoint_from_construction(self):
        self.assertFalse(set(self.fixture["formal_seeds"]) & set(self.fixture["construction_seeds"]))
        self.assertEqual(len(self.fixture["formal_seeds"]),32)

    def test_ineligible_request_cannot_be_injected(self):
        changed=copy.deepcopy(self.data)
        row=next(x for x in changed["rows"] if x["scenario"]=="rights_interrupt")
        row["schedule"][0]["id"]="B2"
        self.assertTrue(self.audit_data(changed)["errors"])

    def test_missing_mandatory_interrupt_rejected(self):
        changed=copy.deepcopy(self.data)
        row=next(x for x in changed["rows"] if x["scenario"]=="rights_interrupt")
        row["schedule"]=[x for x in row["schedule"] if x["id"]!="SYS0"]
        self.assertTrue(self.audit_data(changed)["errors"])


if __name__=="__main__":
    unittest.main()
