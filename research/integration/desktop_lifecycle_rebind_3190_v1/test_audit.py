import copy, tempfile, unittest
from pathlib import Path
import audit

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(); self.repo=Path(self.t.name)
        files={
          "runtime/golden_desktop_demo_v3.py":'def doctor(): pass\ndef run_live(): pass\ndef main(): pass\n',
          "runtime/cli_v1/api.py":'def doctor():\n    return {"side_effect_authority": False}\ndef dispatch():\n    try:\n        pass\n    finally:\n        close = getattr(None,"close",None)\n        cleanup_error = None\n',
          "runtime/core_v1/__init__.py":'admit_program=1\nrequired_capabilities=1\nvalidate_program=1\n',
          "runtime/GOLDEN_DESKTOP_DEMO_V3.md":'First frozen allocation\nAll 57 terminal\n'}
        self.m={"sources":[]}; self.pm={"sources":[]}
        roles={p:list(r) for p,r in audit.EXPECTED_ROLES.items()}
        for p,s in files.items():
            q=self.repo/p; q.parent.mkdir(parents=True,exist_ok=True); q.write_text(s)
            sha=audit.git_blob_sha(q.read_bytes())
            self.m["sources"].append({"path":p,"blob_sha":sha,"roles":roles[p]})
            old=sha if p!="runtime/cli_v1/api.py" else audit.EXPECTED_OLD_API
            self.pm["sources"].append({"path":p,"blob_sha":old,"roles":roles[p]})
        for x in self.m["sources"]:
            if x["path"]=="runtime/cli_v1/api.py": x["blob_sha"]=audit.EXPECTED_NEW_API
        rows=[{"state":s,"mapping":"PASS","authority_granted":False,"task_success_distinct":True,"partial_effects_representable":True,"unknown_fails_closed":True} for s in audit.EXPECTED_ORDER]
        self.pr={"rows_detail":copy.deepcopy(rows)}
        self.r={"status":"PASS_DESKTOP_VERTICAL_SLICE_REBOUND_AUDIT_SCOPED","lifecycle_rows":10,"rows_detail":rows,
                "authority_grants":0,"model_calls":0,"gui_calls":0,"input_calls":0,"network_calls":0,
                "source_changes":[{"path":"runtime/cli_v1/api.py","old_blob":audit.EXPECTED_OLD_API,"new_blob":audit.EXPECTED_NEW_API}]}
    def tearDown(self): self.t.cleanup()
    def test_controls_reject(self):
        api_entry=next(x for x in self.m["sources"] if x["path"]=="runtime/cli_v1/api.py")
        actual=audit.git_blob_sha((self.repo/api_entry["path"]).read_bytes()); api_entry["blob_sha"]=actual
        old_new=audit.EXPECTED_NEW_API
        try:
            audit.EXPECTED_NEW_API=actual
            self.r["source_changes"][0]["new_blob"]=actual
            controls=audit.run_controls(self.repo,self.m,self.r,self.pm,self.pr)
            self.assertEqual(5,len(controls)); self.assertTrue(all(x["rejected"] for x in controls))
        finally: audit.EXPECTED_NEW_API=old_new
    def test_row_change_rejected(self):
        r=copy.deepcopy(self.r); r["rows_detail"][0]["state"]="BAD"
        self.assertIn("row_order",audit.validate(self.repo,self.m,r,self.pm,self.pr))

if __name__=='__main__': unittest.main()
