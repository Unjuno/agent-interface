import importlib.util
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("a05_auditor", HERE / "auditor.py")
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)


class MarkerParserTests(unittest.TestCase):
    def test_geometry_markers_with_ocr_punctuation_variants(self):
        text = "X: 2\nX: 57.627\nY 0\nY 50,000\nw:: 40.000\nH: 30000"
        self.assertEqual(auditor.read_markers(text), auditor.EXPECTED)

    def test_incomplete_crop_does_not_pass(self):
        text = "X: 57.627\nY: 50.000\nW: 40.000\nH: 300"
        self.assertNotEqual(auditor.read_markers(text), auditor.EXPECTED)

    def test_non_task_numbers_do_not_substitute_for_fields(self):
        text = "scale 118 0 100; x: 57.627; y: 50.000; width: 40.000; height: 30.000"
        self.assertNotEqual(auditor.read_markers(text), auditor.EXPECTED)


if __name__ == "__main__":
    unittest.main()
