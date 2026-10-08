import importlib.util, json, tempfile, unittest, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name):
    s=importlib.util.spec_from_file_location(name,HERE/f"{name}.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
audit_mod=load("audit"); runner=load("runner")

def good():
    return {"schema":"x11-private-xvfb-5291-v1","base_main_sha":audit_mod.BASE,"decision":"PASS",
    "wrapper_mount_ns":"mnt:[10]","child_mount_ns":"mnt:[20]","xvfb_proc_mount_ns":"mnt:[20]",
    "mountinfo_line":"5 1 0:5 / /tmp/.X11-unix rw - tmpfs tmpfs rw",
    "readiness":{"width":640,"height":480,"display":":97"},"sigterm_sent":True,
    "xvfb_exit_code":0,"wrapper_exit_code":0,"forced_kill":False,
    "host_socket_before":{"exists":False},"host_socket_after":{"exists":False},
    "checks":{"ready":True,"exit":True}}

class Tests(unittest.TestCase):
    def test_path_containment_and_collisions(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"results").mkdir(); old=runner.HERE; runner.HERE=root
            try:
                self.assertTrue(runner.validate_out(root/"results"/"a").is_relative_to(root/"results"))
                with self.assertRaises(ValueError): runner.validate_out(root/"else")
                (root/"results"/"exists").mkdir()
                with self.assertRaises(FileExistsError): runner.validate_out(root/"results"/"exists")
            finally: runner.HERE=old
    def test_clean_record_passes_and_source_token_is_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"raw.json"; l=p.with_name("runner.log"); l.write_bytes(b"ready\n")
            d=good(); d["mountinfo_line"]=d["mountinfo_line"].replace("tmpfs tmpfs","tmpfs none"); d["log_sha256"]=hashlib.sha256(l.read_bytes()).hexdigest(); p.write_text(json.dumps(d))
            self.assertEqual(audit_mod.audit(p),{"decision":"PASS","reasons":[]})
    def test_independent_mutations_fail_closed(self):
        mutations=[lambda d:d.update(child_mount_ns="mnt:[10]"),lambda d:d.update(xvfb_proc_mount_ns="mnt:[30]"),
        lambda d:d.update(mountinfo_line=d["mountinfo_line"].replace("tmpfs","ext4",1)),
        lambda d:d.update(mountinfo_line=d["mountinfo_line"].replace("/tmp/.X11-unix","/tmp/else")),
        lambda d:d.update(readiness={"width":1}),lambda d:d.update(sigterm_sent=False),
        lambda d:d.update(xvfb_exit_code=-9),lambda d:d.update(wrapper_exit_code=-9),
        lambda d:d.update(forced_kill=True),lambda d:d.update(host_socket_after={"exists":True}),
        lambda d:d.update(decision="STOP"),lambda d:d["checks"].update(exit=False)]
        for mutate in mutations:
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory() as td:
                p=Path(td)/"raw.json"; l=p.with_name("runner.log"); l.write_bytes(b"log\n"); d=good(); d["log_sha256"]=hashlib.sha256(l.read_bytes()).hexdigest(); mutate(d); p.write_text(json.dumps(d))
                self.assertEqual(audit_mod.audit(p)["decision"],"STOP")
    def test_log_tamper_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"raw.json"; l=p.with_name("runner.log"); l.write_bytes(b"altered"); d=good(); d["log_sha256"]="bad"; p.write_text(json.dumps(d))
            self.assertEqual(audit_mod.audit(p)["decision"],"STOP")
if __name__=="__main__": unittest.main(verbosity=2)
