import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("audit_v2",HERE/"audit_v2.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
class SnapshotAuditTests(unittest.TestCase):
    def test_all_snapshots_match_frozen_hashes(self):
        for run in mod.MANIFEST.values():
            for item in run["files"].values():
                self.assertEqual(mod.snapshot_sha(run["commit"],item["path"]),item["sha256"])
    def test_unknown_revision_fails_closed(self):
        with self.assertRaises(ValueError): mod.snapshot_sha("0"*40,"runtime/host_model_ipc_broker_v1.py")
    def test_unbundled_path_fails_closed(self):
        with self.assertRaises(ValueError): mod.snapshot_sha(next(iter(mod.MANIFEST.values()))["commit"],"README.md")
    def test_audits_do_not_call_git(self):
        original=mod.legacy.subprocess.run
        def forbidden(*args,**kwargs): raise AssertionError("git subprocess invoked")
        mod.legacy.subprocess.run=forbidden
        try:
            root=HERE/"evidence"/next(iter(mod.MANIFEST))
            self.assertTrue(mod.audit(root)["disposition"].startswith("PASS_"))
        finally: mod.legacy.subprocess.run=original
if __name__=="__main__": unittest.main()
