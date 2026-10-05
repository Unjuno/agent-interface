import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"src"; FORMAL=ROOT/"results/FORMAL_A01"

class Construction(unittest.TestCase):
    def test_generator_candidate_independent_audit(self):
        subprocess.run([sys.executable,str(SRC/"make_fixture.py")],check=True)
        with tempfile.TemporaryDirectory() as d:
            cand=Path(d)/"candidate.jsonl"; audit=Path(d)/"audit.json"
            subprocess.run([sys.executable,str(SRC/"candidate.py"),str(FORMAL/"public/cases.jsonl"),str(cand)],check=True)
            run=subprocess.run([sys.executable,str(SRC/"auditor.py"),str(FORMAL/"public/cases.jsonl"),str(FORMAL/"oracle/worlds.json"),str(cand),str(audit)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            result=json.loads(audit.read_text())
            self.assertEqual(result["summary"]["false_admissions"],0)
            self.assertEqual(result["summary"]["invalid_fail_closed"],result["summary"]["invalid_controls"])
            self.assertGreaterEqual(result["summary"]["composed_false_unknown_reduction"],.20)
    def test_candidate_output_mutation_is_detected(self):
        subprocess.run([sys.executable,str(SRC/"make_fixture.py")],check=True)
        with tempfile.TemporaryDirectory() as d:
            cand=Path(d)/"candidate.jsonl"; audit=Path(d)/"audit.json"
            subprocess.run([sys.executable,str(SRC/"candidate.py"),str(FORMAL/"public/cases.jsonl"),str(cand)],check=True)
            rows=[json.loads(x) for x in cand.read_text().splitlines()]
            rows[0]["graph"]="UNKNOWN"; cand.write_text("".join(json.dumps(x)+"\n" for x in rows))
            run=subprocess.run([sys.executable,str(SRC/"auditor.py"),str(FORMAL/"public/cases.jsonl"),str(FORMAL/"oracle/worlds.json"),str(cand),str(audit)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            result=json.loads(audit.read_text())
            self.assertEqual(result["disposition"],"PASS_METHOD_SCOPED") # direct controls do not set the composition gate
    def test_candidate_false_admission_control_rejected(self):
        subprocess.run([sys.executable,str(SRC/"make_fixture.py")],check=True)
        with tempfile.TemporaryDirectory() as d:
            cand=Path(d)/"candidate.jsonl"; audit=Path(d)/"audit.json"
            subprocess.run([sys.executable,str(SRC/"candidate.py"),str(FORMAL/"public/cases.jsonl"),str(cand)],check=True)
            rows=[json.loads(x) for x in cand.read_text().splitlines()]
            next(x for x in rows if x["case_id"]=="INVALID_FORBIDDEN_OVERLAP")["graph"]="ADMIT"
            cand.write_text("".join(json.dumps(x)+"\n" for x in rows))
            run=subprocess.run([sys.executable,str(SRC/"auditor.py"),str(FORMAL/"public/cases.jsonl"),str(FORMAL/"oracle/worlds.json"),str(cand),str(audit)],capture_output=True,text=True)
            result=json.loads(audit.read_text())
            self.assertEqual(result["summary"]["false_admissions"],1)
            self.assertEqual(result["disposition"],"FAIL_METHOD")

if __name__=="__main__": unittest.main()
