"""Construction tests for the candidate's frozen network receipt handoff."""
import builtins
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import symtable
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "map01_v39_release_candidate_under_test", HERE / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class CandidateNetworkReceiptTests(unittest.TestCase):
    def test_main_has_no_unbound_global_references(self):
        source = (HERE / "candidate.py").read_text(encoding="utf-8")
        module = symtable.symtable(source, str(HERE / "candidate.py"), "exec")
        main = next(table for table in module.get_children()
                    if table.get_name() == "main")
        module_names = set(module.get_identifiers())
        unbound = [symbol.get_name() for symbol in main.get_symbols()
                   if symbol.is_referenced() and symbol.is_global()
                   and symbol.get_name() not in module_names
                   and not hasattr(builtins, symbol.get_name())]
        self.assertEqual(unbound, [])

    def _verify(self, *, ipv4_routes=""):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        package = root / "package"
        package.mkdir()
        environment = {
            "python_version": sys.version,
            "platform": candidate.platform.platform(),
            "python_packages": "fixture-package==1",
            "dpkg_packages": "fixture-base=1",
        }
        environment_path = package / "ENVIRONMENT.json"
        environment_path.write_text(json.dumps(environment), encoding="utf-8")
        freeze = {
            "allocation_id": "MAP01-V39-RELEASE-TELEMETRY-LIVE-59-T0-20261004-01",
            "sha256": {},
            "runtime_environment_sha256": hashlib.sha256(
                environment_path.read_bytes()).hexdigest(),
        }

        def check_output(command, *, text=False):
            if command[:4] == [sys.executable, "-m", "pip", "freeze"]:
                return "fixture-package==1\n"
            if command[0] == "dpkg-query":
                return "fixture-base=1\n"
            if command == ["ip", "-brief", "link"]:
                return "ip6tnl0 DOWN\nlo DOWN\nsit0 DOWN\ntunl0 DOWN\n"
            if command == ["ip", "route"]:
                return ipv4_routes
            if command == ["ip", "-6", "route"]:
                return ""
            raise AssertionError(f"unexpected command: {command!r}")

        with mock.patch.object(candidate, "ROOT", root), \
                mock.patch.object(candidate, "PACKAGE", package), \
                mock.patch.object(candidate.socket, "if_nameindex", return_value=[
                    (1, "lo"), (2, "ip6tnl0"), (3, "sit0"), (4, "tunl0")]), \
                mock.patch.object(candidate.subprocess, "check_output",
                                  side_effect=check_output):
            receipt = candidate.verify_frozen(freeze)
        return freeze, receipt

    def test_verified_network_snapshot_is_returned_for_candidate_record(self):
        freeze, receipt = self._verify()
        expected = {
            "network_interfaces": ["ip6tnl0", "lo", "sit0", "tunl0"],
            "network_link_states": {
                "ip6tnl0": "DOWN", "lo": "DOWN", "sit0": "DOWN", "tunl0": "DOWN",
            },
            "network_ipv4_routes": "",
            "network_ipv6_routes": "",
        }
        self.assertEqual(receipt, expected)
        row = candidate.initial_candidate_record(freeze, receipt)
        for name, value in expected.items():
            self.assertEqual(row[name], value)
        self.assertFalse(row["candidate_completed"])

    def test_nonempty_route_stops_before_returning_a_network_receipt(self):
        with self.assertRaisesRegex(RuntimeError, "STOP_NETWORK_NAMESPACE"):
            self._verify(ipv4_routes="default via 192.0.2.1 dev eth0\n")

    def test_incomplete_network_receipt_fails_closed(self):
        freeze = {
            "allocation_id": "test",
            "runtime_environment_sha256": "environment",
        }
        for receipt in ({"network_interfaces": ["lo"]}, None):
            with self.subTest(receipt=receipt):
                with self.assertRaisesRegex(
                        RuntimeError, "STOP_NETWORK_RECEIPT_INCOMPLETE"):
                    candidate.initial_candidate_record(freeze, receipt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
