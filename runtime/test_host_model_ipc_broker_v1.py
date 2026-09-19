from pathlib import Path
import unittest


class HostBrokerContractTest(unittest.TestCase):
    def test_maps_container_repo_paths(self):
        from runtime.host_model_ipc_broker_v1 import host_path
        self.assertEqual(host_path("/repo/runtime/a.png", Path("C:/repo")), "C:/repo/runtime/a.png")
        self.assertIsNone(host_path(None, Path("C:/repo")))

    def test_broker_is_non_authoritative(self):
        source = Path(__file__).with_name("host_model_ipc_broker_v1.py").read_text()
        self.assertIn('"authority_granted": False', source)


if __name__ == "__main__":
    unittest.main()
