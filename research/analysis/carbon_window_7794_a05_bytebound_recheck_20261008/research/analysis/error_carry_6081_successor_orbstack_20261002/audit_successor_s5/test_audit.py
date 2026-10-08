import json, unittest
from fractions import Fraction as R
from pathlib import Path
import audit

HERE=Path(__file__).parent
FIXTURE=json.loads((HERE.parent/"fixture.json").read_text())

class AuditConstruction(unittest.TestCase):
    def test_refusal_rows_are_schedule_free(self):
        case=dict(FIXTURE["cases"][-1],action_set="4way")
        result=audit.replay(case,FIXTURE["action_sets"]["4way"],audit.POLICY[0])
        self.assertEqual(result,{"status":"REFUSE_UNKNOWN_CALIBRATION","moves":[],"positions":[],"release":True,"switches":0})
    def test_outside_hull_is_dictionary_specific(self):
        case=dict(FIXTURE["cases"][-2],action_set="4way")
        self.assertEqual(audit.replay(case,FIXTURE["action_sets"]["4way"],audit.POLICY[0])["status"],"REFUSE_OUTSIDE_HULL")
        case["action_set"]="8way"
        self.assertEqual(audit.replay(case,FIXTURE["action_sets"]["8way"],audit.POLICY[0])["status"],"SCHEDULED")
    def test_stationary_nearest_arms_equal(self):
        rows=audit.reconstruct(FIXTURE)
        self.assertEqual(len(rows),80)
        for name in FIXTURE["action_sets"]:
            for case in FIXTURE["cases"]:
                found=[r["result"] for r in rows if r["action_set"]==name and r["case"]==case["id"] and r["policy"] in audit.POLICY[:2]]
                self.assertEqual(found[0],found[1])
    def test_raw_corruption_is_rejected(self):
        good={"schema":"error-carry-raw-v1","rows":audit.reconstruct(FIXTURE)}
        bad=json.loads(json.dumps(good)); bad["rows"].pop()
        with self.assertRaisesRegex(ValueError,"FAIL_RAW_RECONSTRUCTION"):
            audit.evaluate(FIXTURE,bad)
    def test_safety_audits_every_prefix(self):
        case={"id":"box","intent":["1","0"],"horizon":2,"max_switches":2,"box":[-1,1,-1,1],"action_set":"4way"}
        row=audit.replay(case,FIXTURE["action_sets"]["4way"],audit.POLICY[0])
        self.assertEqual(row["envelope_violations"],1)
        self.assertEqual(row["status"],"UNSAFE_PREFIX")

if __name__=="__main__": unittest.main()
