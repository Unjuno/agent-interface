import unittest

from run_candidate_t0_02 import frozen_image_digest


class RunnerSchemaTests(unittest.TestCase):
    def test_runner_reads_nested_container_image_digest(self):
        freeze = {"container": {"image_digest": "sha256:abc"}}
        self.assertEqual(frozen_image_digest(freeze), "sha256:abc")


if __name__ == "__main__":
    unittest.main()
