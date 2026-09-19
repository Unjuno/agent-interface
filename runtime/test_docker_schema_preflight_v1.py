from pathlib import Path
import unittest


class DockerSchemaPreflightAdapterTest(unittest.TestCase):
    def test_boundary_and_fail_closed_contract(self):
        source = Path(__file__).with_name("docker_schema_preflight_v1.py").read_text()
        self.assertIn("container-to-host-model-ipc", source)
        self.assertIn("STOP_MALFORMED_MODEL_RESPONSE", source)
        self.assertIn('"authority_granted": False', source)


if __name__ == "__main__":
    unittest.main()
