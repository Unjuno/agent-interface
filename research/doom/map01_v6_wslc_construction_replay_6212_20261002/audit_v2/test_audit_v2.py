"""Adversarial checks for the audit-v2 exact-output gate."""
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest

MODULE = pathlib.Path(__file__).with_name("audit_v2.py")
spec = importlib.util.spec_from_file_location("audit_v2", MODULE)
audit_v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_v2)

class AuditV2Tests(unittest.TestCase):
    def check_audit(self, mutation=None):
        rows = [{"script": n, "stdout": out, "exit_code": 0, "wall_ms": 1}
                for n, out in audit_v2.EXPECTED]
        if mutation:
            mutation(rows)
        result = {"schema":"wslc-construction-replay-v1","all_children_exit_zero":True,
                  "children":rows,"cgroup":{"cpu.max":"200000 100000","memory.max":"536870912",
                  "memory.peak":"1","memory.swap.max":"max"}}
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)
            manifest = {"files":[]}
            for i in range(10):
                name=f"source{i}.py"
                (p/name).write_text("x")
                manifest["files"].append({"path":name,
                    "blob_sha1":hashlib.sha1(b"blob 1\0x").hexdigest(),
                    "sha256":hashlib.sha256(b"x").hexdigest()})
            (p/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest))
            return audit_v2.audit(p,p,result)

    def test_exact_recorded_stdout_passes(self):
        self.assertEqual(self.check_audit()["errors"], [])

    def test_missing_line_is_rejected(self):
        def mutate(rows):
            rows[0]["stdout"] = rows[0]["stdout"].replace("PASS test_boundary_phase_is_retained\n", "")
        self.assertIn("exact_stdout:test_map01_recovery_cover_mechanism_v6.py",
                      self.check_audit(mutate)["errors"])

    def test_extra_failure_text_is_rejected(self):
        def mutate(rows):
            rows[1]["stdout"] += "FAIL unexpected\n"
        self.assertIn("exact_stdout:test_map01_recovery_cover_mechanism_v5.py",
                      self.check_audit(mutate)["errors"])

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AuditV2Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
