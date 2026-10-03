"""Finite factory-boundary characterization; no OS/backend operations."""
import hashlib
import itertools
import json
from pathlib import Path
import sys

from runtime.kernel import BackendInfo, BackendRegistry, ContractError, SupportLevel

METHODS = ("probe", "observe", "execute", "release_all")


def main():
    rows = []
    for states in itertools.product(("missing", "noncallable", "callable"), repeat=4):
        counts = dict(probe=0, observe=0, execute=0, release_all=0)

        def probe(self):
            counts["probe"] += 1
            return BackendInfo("matrix", "test", SupportLevel.EXPERIMENTAL, frozenset())

        def operating(name):
            def method(self, *args):
                counts[name] += 1
                raise AssertionError("registry performed backend I/O")
            return method

        attrs = {}
        for name, state in zip(METHODS, states):
            if state == "callable":
                attrs[name] = probe if name == "probe" else operating(name)
            elif state == "noncallable":
                attrs[name] = None
        backend = type("MatrixBackend", (), attrs)()
        registry = BackendRegistry()
        registry.register("test", lambda: backend)
        try:
            result = registry.create("test")
            outcome = "accepted" if result is backend else "wrong_object"
        except ContractError:
            outcome = "contract_rejected"
        except Exception as error:
            outcome = type(error).__name__
        rows.append(dict(states=list(states), outcome=outcome, calls=dict(counts)))
    root = Path(__file__).resolve().parents[3]
    source = root / "runtime/kernel/backend.py"
    record = dict(schema="backend-factory-matrix-v1", python=sys.version,
                  backend_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), rows=rows)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
