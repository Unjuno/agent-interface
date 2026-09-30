import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CallerNestingTests(unittest.TestCase):
    def test_all_local_release_calls_are_classified(self):
        tree = ast.parse((ROOT / "source" / "owner_v10.py").read_text())
        owner_run = next(n for n in ast.walk(tree)
                         if isinstance(n, ast.FunctionDef) and n.name == "_run")
        releases = [n for n in ast.walk(owner_run)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == "release"]
        self.assertEqual(len(releases), 4)

    def test_universal_release_nesting_gate(self):
        tree = ast.parse((ROOT / "source" / "owner_v10.py").read_text())
        owner_run = next(n for n in ast.walk(tree)
                         if isinstance(n, ast.FunctionDef) and n.name == "_run")
        explicit = []
        for node in ast.walk(owner_run):
            if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
                text = ast.unparse(node.test)
                if "op in ('release', 'close')" in text or "op == 'release'" in text:
                    explicit.extend(n for n in ast.walk(node)
                                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                                    and n.func.id == "release")
        self.assertEqual(len(explicit), 1)
        all_release_nodes = [n for n in ast.walk(owner_run)
                             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                             and n.func.id == "release"]
        self.assertEqual(len(all_release_nodes), 4)
        # Universal claim is false because three release paths are not the
        # queued explicit release operation, and execute after earlier calls.
        self.assertFalse(len(explicit) == len(all_release_nodes))

    def test_wrapper_times_explicit_up_but_not_deferred_owner_cleanup(self):
        tree = ast.parse((ROOT / "source" / "wrapper_v3.py").read_text())
        call = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "call")
        source = ast.unparse(call)
        self.assertIn("operation not in ('up', 'button_up')", source)
        self.assertIn("operation in ('release', 'close')", source)
        self.assertIn("release_call_started_ns = time.perf_counter_ns()", source)
        self.assertIn("release_call_returned_ns = time.perf_counter_ns()", source)
        self.assertIn("self._inner.call(operation, lease, key)", source)
        owner_source = (ROOT / "source" / "owner_v10.py").read_text()
        self.assertIn("release('expired' if expired else", owner_source)
        self.assertIn("release('stop_requested')", owner_source)
        self.assertIn("release('thread_exit')", owner_source)

    def test_direct_owner_brackets_cover_request_and_xsync_but_not_physical_delivery(self):
        tree = ast.parse((ROOT / "source" / "owner_v10.py").read_text())
        release = next(n for n in ast.walk(tree)
                       if isinstance(n, ast.FunctionDef) and n.name == "release")
        source = ast.unparse(release)
        release_req = source.index("xtest.fake_input(d, X.KeyRelease, code)")
        sync = source.index("d.sync()")
        self.assertLess(release_req, sync)
        self.assertNotIn("caller", source)
        self.assertNotIn("physical", source)
        self.assertIn("verified_ns", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
