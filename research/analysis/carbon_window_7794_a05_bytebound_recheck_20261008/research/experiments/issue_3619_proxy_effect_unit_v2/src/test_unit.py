import tempfile
import unittest
from pathlib import Path
import ast
import inspect

from proxy import render
from runner import wait_state


class ProxySurfaceTests(unittest.TestCase):
    def test_wait_state_accepts_the_pid_hint_used_by_allocation(self):
        self.assertIn("pid_hint", inspect.signature(wait_state).parameters)
        tree=ast.parse(Path(__file__).with_name("runner.py").read_text())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="wait_state"]
        self.assertTrue(calls)
        self.assertTrue(all(any(k.arg=="pid_hint" for k in call.keywords) for call in calls))

    def test_image_is_deterministic_and_state_bound_by_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b, c = (Path(tmp) / n for n in ("a.ppm", "b.ppm", "c.ppm"))
            render(0, 1, a); render(0, 1, b); render(1, 2, c)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertNotEqual(a.read_bytes(), c.read_bytes())
            self.assertTrue(a.read_bytes().startswith(b"P6\n320 120\n255\n"))


if __name__ == "__main__":
    unittest.main()
