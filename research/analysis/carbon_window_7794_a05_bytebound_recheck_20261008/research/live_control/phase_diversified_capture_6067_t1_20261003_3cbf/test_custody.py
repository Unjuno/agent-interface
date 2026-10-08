"""Terminal execution receipt is distinct from scientific success."""
import copy
import unittest
from verify_evidence import check_runtime

def runtime():
    return {"Image": "sha256:test", "RestartCount": 0,
            "State": {"Running": False, "OOMKilled": False, "ExitCode": 2},
            "Config": {"User": "501:501"},
            "HostConfig": {"NanoCpus": 1_000_000_000, "Memory": 536870912,
                "MemorySwap": 536870912, "PidsLimit": 64, "NetworkMode": "none",
                "ReadonlyRootfs": True, "CapDrop": ["ALL"], "Privileged": False,
                "SecurityOpt": ["no-new-privileges"], "Devices": [], "DeviceRequests": []}}

class CustodyTests(unittest.TestCase):
    def test_terminal_stop_is_retained_not_success(self):
        self.assertEqual(check_runtime(runtime(), "sha256:test"), 2)

    def test_runtime_drift_and_fake_terminality_are_refused(self):
        variants = []
        for path, value in [(("State", "Running"), True), (("State", "OOMKilled"), True),
                            (("State", "ExitCode"), True), (("HostConfig", "NetworkMode"), "default"),
                            (("HostConfig", "Memory"), 0), (("HostConfig", "Privileged"), True)]:
            r = runtime(); r[path[0]][path[1]] = value; variants.append(r)
        r = runtime(); r["Image"] = "wrong"; variants.append(r)
        r = runtime(); r["RestartCount"] = 1; variants.append(r)
        for r in variants:
            with self.subTest(r=r):
                with self.assertRaises(ValueError):
                    check_runtime(r, "sha256:test")

if __name__ == "__main__":
    unittest.main()
