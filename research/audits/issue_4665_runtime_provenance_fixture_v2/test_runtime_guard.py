import unittest

from runtime_guard import RUNTIME_FIELDS, validate_runtime


EXPECTED = {
    "docker_engine": "29.8.0",
    "daemon_platform": "linux/x86_64",
    "image_id": "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
    "image_platform": "linux/amd64",
    "python": "3.12.14",
}
RECEIPT = {key: value for key, value in EXPECTED.items() if key != "python"}


class RuntimeGuardTests(unittest.TestCase):
    def test_exact_receipt_passes(self):
        self.assertEqual(validate_runtime(RECEIPT, EXPECTED, EXPECTED["python"]), [])

    def test_each_observed_runtime_mismatch_stops(self):
        for field in RUNTIME_FIELDS:
            with self.subTest(field=field):
                receipt = dict(RECEIPT)
                python = EXPECTED["python"]
                if field == "python":
                    python = "0.0.0"
                else:
                    receipt[field] = "mismatch"
                self.assertTrue(validate_runtime(receipt, EXPECTED, python))

    def test_missing_or_malformed_receipt_stops(self):
        self.assertTrue(validate_runtime({}, EXPECTED, EXPECTED["python"]))
        self.assertTrue(validate_runtime(None, EXPECTED, EXPECTED["python"]))


if __name__ == "__main__":
    unittest.main()
