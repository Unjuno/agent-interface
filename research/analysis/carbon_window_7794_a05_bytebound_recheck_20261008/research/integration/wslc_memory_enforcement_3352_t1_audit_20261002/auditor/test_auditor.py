import importlib.util
import tempfile
import unittest
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_mem", HERE / "auditor.py")
audit_mem = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mem)
SOURCE = Path("/mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/wslc-memory-t0")

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(SOURCE, self.root, dirs_exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reconstructs_scoped_failure(self):
        result = audit_mem.audit(self.root)
        self.assertEqual(result["status"], "PASS_INDEPENDENT_AUDIT_SCOPED")
        self.assertEqual([x["allocated_mib"] for x in result["arms"]], [384, 384])
        self.assertEqual([x["memory_max_bytes"] for x in result["arms"]], [536870912, 134217728])

    def mutate_raw(self, old, new):
        p = self.root / "raw.log"
        p.write_text(p.read_text().replace(old, new), encoding="utf-8")

    def test_rejects_claimed_oom_or_changed_allocation(self):
        self.mutate_raw("ALLOCATED_MIB=384", "ALLOCATED_MIB=128")
        with self.assertRaises(ValueError): audit_mem.audit(self.root)

    def test_rejects_wrong_reported_memory_max(self):
        self.mutate_raw("memory.max 134217728", "memory.max 134217729")
        with self.assertRaises(ValueError): audit_mem.audit(self.root)

    def test_rejects_missing_warning(self):
        self.mutate_raw("wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.", "warning absent")
        with self.assertRaises(ValueError): audit_mem.audit(self.root)

    def test_rejects_command_arm_mismatch(self):
        p = self.root / "commands.txt"
        p.write_text(p.read_text().replace("--cpus 1 --memory 128M", "--cpus 2 --memory 128M"), encoding="utf-8")
        with self.assertRaises(ValueError): audit_mem.audit(self.root)

    def test_rejects_source_hash_drift(self):
        p = self.root / "probe.py"
        p.write_text(p.read_text() + "# mutation\n", encoding="utf-8")
        with self.assertRaises(ValueError): audit_mem.audit(self.root)

if __name__ == "__main__":
    unittest.main()
