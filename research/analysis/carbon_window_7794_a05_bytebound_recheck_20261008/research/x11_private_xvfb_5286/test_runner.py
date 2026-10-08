import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit", HERE / "audit.py")
audit_mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit_mod)
spec2 = importlib.util.spec_from_file_location("runner", HERE / "runner.py")
runner = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(runner)


def clean_record():
    return {"schema":"x11-private-xvfb-5286-v1", "base_main_sha":audit_mod.BASE,
        "decision":"PASS", "wrapper_mount_ns":"mnt:[100]", "child_mount_ns":"mnt:[123]", "xvfb_proc_mount_ns":"mnt:[123]", "xvfb_pid":456,
        "mountinfo_line":"44 30 0:44 / /tmp/.X11-unix rw,nosuid,nodev - tmpfs tmpfs rw,mode=1777",
        "readiness":{"width":640,"height":480}, "sigterm_sent":True, "xvfb_exit_code":0,
        "forced_kill":False, "host_socket_before":{"exists":False}, "host_socket_after":{"exists":False},
        "checks":{"readiness":True,"clean_sigterm":True,"namespace_bound":True,"mount_private_tmpfs":True,"host_socket_unchanged":True}}


class RunnerAuditTests(unittest.TestCase):
    def test_output_containment_and_collision(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root/"results").mkdir()
            old = runner.HERE; runner.HERE = root
            try:
                self.assertTrue(runner.validate_out(root/"results"/"new").is_relative_to(root/"results"))
                with self.assertRaises(ValueError): runner.validate_out(root/"elsewhere")
                (root/"results"/"exists").mkdir()
                with self.assertRaises(FileExistsError): runner.validate_out(root/"results"/"exists")
            finally: runner.HERE = old

    def test_independent_audit_accepts_complete_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"raw.json"; log=p.with_name("runner.log"); log.write_bytes(b"raw Xvfb output\n")
            d=clean_record(); import hashlib; d["log_sha256"]=hashlib.sha256(log.read_bytes()).hexdigest()
            p.write_text(json.dumps(d))
            self.assertEqual(audit_mod.audit(p), {"decision":"PASS","reasons":[]})

    def test_mount_source_token_is_not_part_of_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"raw.json"; log=p.with_name("runner.log"); log.write_bytes(b"raw Xvfb output\n")
            d=clean_record(); d["mountinfo_line"]=d["mountinfo_line"].replace("tmpfs tmpfs", "tmpfs none")
            import hashlib; d["log_sha256"]=hashlib.sha256(log.read_bytes()).hexdigest(); p.write_text(json.dumps(d))
            self.assertEqual(audit_mod.audit(p), {"decision":"PASS","reasons":[]})

    def test_mutations_each_fail_closed(self):
        mutations = [
            lambda d: d.update(child_mount_ns="mnt:[999]"),
            lambda d: d.update(xvfb_proc_mount_ns="mnt:[999]"),
            lambda d: d.update(child_mount_ns=d["wrapper_mount_ns"], xvfb_proc_mount_ns=d["wrapper_mount_ns"]),
            lambda d: d.update(mountinfo_line=d["mountinfo_line"].replace("tmpfs", "ext4", 1)),
            lambda d: d.update(mountinfo_line=d["mountinfo_line"].replace("/tmp/.X11-unix", "/tmp/other")),
            lambda d: d.update(readiness={"width":800,"height":600}),
            lambda d: d.update(sigterm_sent=False),
            lambda d: d.update(forced_kill=True),
            lambda d: d.update(xvfb_exit_code=-9),
            lambda d: d.update(host_socket_after={"exists":True}),
            lambda d: d.update(decision="STOP"),
            lambda d: d["checks"].update(clean_sigterm=False),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as td:
                p=Path(td)/"raw.json"; log=p.with_name("runner.log"); log.write_bytes(b"log\n")
                d=clean_record(); import hashlib; d["log_sha256"]=hashlib.sha256(log.read_bytes()).hexdigest(); mutate(d); p.write_text(json.dumps(d))
                self.assertEqual(audit_mod.audit(p)["decision"], "STOP")

    def test_missing_log_or_tampered_log_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"raw.json"; d=clean_record(); d["log_sha256"]="wrong"; p.write_text(json.dumps(d))
            self.assertEqual(audit_mod.audit(p)["decision"], "STOP")
            p.with_name("runner.log").write_text("changed")
            self.assertIn("runner log hash mismatch", audit_mod.audit(p)["reasons"])


if __name__ == "__main__": unittest.main(verbosity=2)
