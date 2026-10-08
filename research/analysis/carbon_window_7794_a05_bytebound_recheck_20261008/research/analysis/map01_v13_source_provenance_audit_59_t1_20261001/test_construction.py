import hashlib
import json
import unittest
from unittest.mock import patch

import auditor
import candidate


class CurrentMainSourceClosureTests(unittest.TestCase):
    def setUp(self):
        self.fixture={"source_commit":"main-freeze","prereg_path":"prereg.json","historical_allocation_id":"old-allocation"}
        self.files={"src/a.py":b"alpha\n","src/b.py":b"bravo\n"}
        self.prereg={"source_sha256":{"src/a.py":hashlib.sha256(self.files["src/a.py"]).hexdigest()},
                     "canonical_upstream_sha256":{"src/b.py":hashlib.sha256(self.files["src/b.py"]).hexdigest()}}
        self.prereg_raw=json.dumps(self.prereg).encode()

    def raw_candidate(self, files=None):
        files=self.files if files is None else files
        pins={}
        for group in ("source_sha256","canonical_upstream_sha256"):
            for path,digest in self.prereg[group].items(): pins.setdefault(path,set()).add(digest)
        rows=[]
        for path in sorted(pins):
            data=files.get(path)
            rows.append({"path":path,"expected_sha256":sorted(pins[path]),
                         "actual_sha256":hashlib.sha256(data).hexdigest() if data is not None else None,
                         "present":data is not None})
        return {"source_commit":"main-freeze","prereg_path":"prereg.json","expected_source_path_count":len(pins),"rows":rows}

    def run_audit(self,files=None,raw=None):
        files=self.files if files is None else files
        def get(_root,_commit,path):
            return self.prereg_raw if path=="prereg.json" else files.get(path)
        with patch.object(auditor,"git_object",side_effect=get):
            return auditor.verify(None,self.fixture,self.raw_candidate(files) if raw is None else raw)

    def test_exact_complete_union_passes_only_source_layer(self):
        result=self.run_audit()
        self.assertEqual("PASS_SOURCE_CLOSURE_ONLY",result["disposition"])
        self.assertEqual(2,result["independently_verified_path_count"])
        self.assertFalse(result["live_validation_authorized"])

    def test_script_derived_repository_root_is_checkout_root(self):
        self.assertTrue((candidate.ROOT/".git").exists())
        self.assertEqual(candidate.ROOT.resolve(),candidate.Path(__file__).resolve().parents[3])

    def test_changed_git_blob_is_retained_as_source_drift(self):
        changed={"src/a.py":b"new\n","src/b.py":self.files["src/b.py"]}
        result=self.run_audit(files=changed)
        self.assertEqual("FAIL_PINNED_SOURCE_DRIFT",result["disposition"])
        self.assertEqual(["src/a.py"],result["drift_paths"])

    def test_missing_candidate_path_fails_integrity(self):
        raw=self.raw_candidate()
        raw["rows"]=raw["rows"][:1]
        result=self.run_audit(raw=raw)
        self.assertEqual("FAIL_AUDIT_INTEGRITY",result["disposition"])
        self.assertIn("candidate-path-set-mismatch",result["errors"])

    def test_conflicting_duplicate_preregistration_pins_fail_closed(self):
        self.prereg["canonical_upstream_sha256"]["src/a.py"]="0"*64
        self.prereg_raw=json.dumps(self.prereg).encode()
        result=self.run_audit()
        self.assertEqual("FAIL_PINNED_SOURCE_DRIFT",result["disposition"])
        self.assertEqual(["src/a.py"],result["drift_paths"])


if __name__=="__main__":
    unittest.main(verbosity=2)
