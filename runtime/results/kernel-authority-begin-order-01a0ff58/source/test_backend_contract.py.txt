"""Registry admission checks; no backend I/O is performed."""
import unittest

from runtime.kernel import (
    BackendInfo, BackendRegistry, Capability, ContractError, SupportLevel,
)


class CompleteBackend:
    def __init__(self):
        self.probe_calls = 0

    def probe(self):
        self.probe_calls += 1
        return BackendInfo(
            "contract-fixture", "test", SupportLevel.EXPERIMENTAL,
            frozenset({Capability.OBSERVE_SCREEN, Capability.RELEASE_ALL}),
        )

    def observe(self):
        raise AssertionError("registry must not perform observation")

    def execute(self, request):
        raise AssertionError("registry must not perform input")

    def release_all(self):
        raise AssertionError("registry must not perform release")


class BackendAdmissionTests(unittest.TestCase):
    def test_missing_protocol_methods_are_rejected_before_probe(self):
        methods = ("probe", "observe", "execute", "release_all")
        for absent in methods:
            with self.subTest(absent=absent):
                attrs = {name: getattr(CompleteBackend, name)
                         for name in methods if name != absent}
                attrs["__init__"] = CompleteBackend.__init__
                backend = type("IncompleteBackend", (), attrs)()
                registry = BackendRegistry()
                registry.register("test", lambda: backend)
                with self.assertRaises(ContractError):
                    registry.create("test")
                self.assertEqual(backend.probe_calls, 0)

    def test_noncallable_protocol_methods_are_rejected_before_probe(self):
        for method in ("probe", "observe", "execute", "release_all"):
            for replacement in (None, False, 0, "method"):
                with self.subTest(method=method, replacement=replacement):
                    backend = CompleteBackend()
                    setattr(backend, method, replacement)
                    registry = BackendRegistry()
                    registry.register("test", lambda: backend)
                    with self.assertRaises(ContractError):
                        registry.create("test")
                    self.assertEqual(backend.probe_calls, 0)

    def test_complete_backend_is_returned_without_operating_it(self):
        backend = CompleteBackend()
        registry = BackendRegistry()
        registry.register("test", lambda: backend)
        self.assertIs(registry.create("test"), backend)
        self.assertEqual(backend.probe_calls, 1)


if __name__ == "__main__":
    unittest.main()
