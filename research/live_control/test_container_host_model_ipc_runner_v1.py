from pathlib import Path
import unittest


class ContainerHostIpcContractTest(unittest.TestCase):
    def test_runner_is_fail_closed_and_shared_volume_bound(self):
        source = Path(__file__).with_name("container_host_model_ipc_runner_v1.py").read_text()
        self.assertIn("HOST_MODEL_IPC_DIR", source)
        self.assertIn('"authority_granted": False', source)
        self.assertIn("response timeout", source)

    def test_runner_has_no_direct_input_api(self):
        source = Path(__file__).with_name("container_host_model_ipc_runner_v1.py").read_text()
        self.assertNotIn("dispatch_golden_v3", source)
        self.assertNotIn("pointer_button", source)
        self.assertNotIn("input.text", source)


if __name__ == "__main__":
    unittest.main()
