"""Recheck the published Calc packet without launching its producers.

Pass an exact Git archive extraction or a fully materialized packet directory.
Only the historical mutation reader is adapted, to normalize overlay paths on
Windows. No historical file or expected assertion is changed.
"""
import argparse
import hashlib
import importlib
import io
import json
from pathlib import Path
import sys
import unittest


def check(packet):
    packet = Path(packet).resolve()
    manifest_count = 0
    for line in (packet / "PUBLICATION-SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        path = (packet / name).resolve()
        if not path.is_relative_to(packet):
            raise ValueError("unowned manifest path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("publication manifest mismatch: " + name)
        manifest_count += 1

    # These inspected modules only read retained files. In particular do not
    # import keeper/composition/collect_usage or invoke verify_usage.__main__,
    # which would overwrite a historical report.
    sys.path.insert(0, str(packet))
    audit_module = importlib.import_module("verify")
    mutations = importlib.import_module("test_verify")
    mechanics = audit_module.audit(packet)

    class PortableMutations(mutations.RetainedAuditTests):
        def read(self, relative):
            name = Path(relative).as_posix()
            if name in self.overlay:
                return self.overlay[name]
            return (packet / relative).read_bytes()

    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PortableMutations)
    )
    sys.stderr.write(stream.getvalue())
    if result.testsRun != 18 or not result.wasSuccessful():
        raise ValueError("historical semantic mutations failed")

    sys.path.insert(0, str(packet / "usage-02"))
    usage = importlib.import_module("verify_usage").verify(check_original=False)
    return {
        "status": "PASS_SAVED_RECONSTRUCTION",
        "publication_manifest_members": manifest_count,
        "mechanics": mechanics,
        "portable_mutation_tests": result.testsRun,
        "usage": usage,
        "new_live_allocations": 0,
        "scope": "Published artifact consistency, saved workbook scoring and joint usage reconstruction only; original private session not checked; no route cost, current-source live qualification or physical release bound.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.packet), indent=2))
