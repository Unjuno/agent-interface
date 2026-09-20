import unittest
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import runner


class ClassifierControls(unittest.TestCase):
    def test_eight_frozen_controls(self):
        for name, (source, expected) in runner.CONTROLS.items():
            with self.subTest(name=name):
                rows = runner.classify(source)
                actual = [r["call"] for r in rows if r["context"] not in
                          {"main_guard_test", "main_guard_else"}]
                self.assertEqual(expected, actual)

    def test_unguarded_historical_target_is_module_call(self):
        source = "try:\n    session.main()\nfinally:\n    save()\n"
        rows = runner.module_calls(__import__("ast").parse(source))
        self.assertIn({"call": "main", "context": "module", "line": 2}, rows)


if __name__ == "__main__":
    unittest.main()
