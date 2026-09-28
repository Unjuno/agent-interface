from __future__ import annotations

import base64
import copy
import hashlib
import json
import unittest
from pathlib import Path

import audit
import host_boundary

HERE = Path(__file__).resolve().parent
SEED = HERE.parents[2] / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"


class HostBoundaryConstructionTests(unittest.TestCase):
    def test_frozen_schedule_is_seven_by_four(self):
        self.assertEqual(len(host_boundary.PHASES), 7)
        self.assertEqual(len(host_boundary.GENERATIONS), 7)
        self.assertEqual(host_boundary.READERS, 4)
        self.assertEqual(len(host_boundary.PHASES) * host_boundary.READERS, 28)

    def test_seed_and_allocation_bound_successors(self):
        raw = SEED.read_bytes()
        self.assertEqual(host_boundary.sha(raw), host_boundary.SEED_SHA256)
        seed = json.loads(raw)
        packages = [host_boundary.package_for(seed, generation) for generation in host_boundary.GENERATIONS]
        self.assertEqual(len(set(packages)), 7)
        for generation, package in zip(host_boundary.GENERATIONS, packages, strict=True):
            value = json.loads(package)
            self.assertEqual(value["generation"], generation)
            self.assertEqual(value["provenance"]["allocation"], host_boundary.ALLOCATION)
            self.assertEqual(audit.sha(audit.canonical({k: v for k, v in value.items() if k != "payload_sha256"})), value["payload_sha256"])

    def test_auditor_rejects_wrong_seed_identity(self):
        errors = audit.audit_raw({}, b"not the frozen seed")
        self.assertIn("seed_sha256", errors)
        self.assertIn("schema", errors)

    def test_partial_is_strict_prefix_by_construction(self):
        seed = json.loads(SEED.read_bytes())
        full = host_boundary.package_for(seed, host_boundary.GENERATIONS[0])
        split = max(1, len(full) // 3)
        self.assertLess(split, len(full))
        self.assertEqual(full[:split], full[:split])
        self.assertNotEqual(full[:split], full)

    def test_independent_auditor_accepts_complete_synthetic_contract_and_rejects_mutation(self):
        seed_raw = SEED.read_bytes()
        seed = json.loads(seed_raw)
        freeze = json.loads((HERE / "FREEZE.json").read_text())
        raw = {"schema": "needle-publication-host-boundary-raw-v1",
               "allocation": host_boundary.ALLOCATION, "issue": host_boundary.ISSUE,
               "status": "CAPTURED", "docker_invocations": 0, "container_id": None,
               "seed_sha256": host_boundary.sha(seed_raw), "seed_git_blob": host_boundary.blob_id(seed_raw),
               "seed_bytes": len(seed_raw), "phases": list(host_boundary.PHASES),
               "generations": list(host_boundary.GENERATIONS), "readers_per_phase": host_boundary.READERS,
               "source_commit": freeze["base_main_sha"],
               "source_tree": "9" * 40, "frozen_main": freeze["base_main_sha"],
               "source_sha256": freeze["source_sha256"],
               "candidate_sha256": {}, "atomic_rows": [], "unsafe_rows": []}
        previous = seed_raw
        for phase_index, (phase, generation) in enumerate(zip(host_boundary.PHASES, host_boundary.GENERATIONS, strict=True)):
            expected = host_boundary.package_for(seed, generation)
            raw["candidate_sha256"][str(generation)] = host_boundary.sha(expected)
            base = (phase_index + 1) * 100
            for reader in range(host_boundary.READERS):
                pid = (phase_index + 1) * 10 + reader
                raw["atomic_rows"].append({"phase": phase, "reader": reader, "pid": pid,
                    "generation": generation, "child_exit_codes": [0] * host_boundary.READERS,
                    "fd_open_ns": base - 10, "replace_start_ns": base, "replace_return_ns": base + 1,
                    "fd_read_start_ns": base + 2, "fd_read_end_ns": base + 3,
                    "fresh_open_ns": base + 4, "fresh_read_end_ns": base + 5,
                    "held_b64": base64.b64encode(previous).decode(), "held_sha256": hashlib.sha256(previous).hexdigest(),
                    "fresh_b64": base64.b64encode(expected).decode(), "fresh_sha256": hashlib.sha256(expected).hexdigest()})
                split = max(1, len(expected) // 3)
                partial = expected[:split]
                raw["unsafe_rows"].append({"phase": phase, "reader": reader, "pid": pid + 1000,
                    "generation": generation, "child_exit_codes": [0] * host_boundary.READERS,
                    "fd_open_ns": base - 10, "write_start_ns": base, "truncate_ns": base + 1,
                    "partial_complete_ns": base + 2, "read_start_ns": base + 3, "read_end_ns": base + 4,
                    "fresh_open_ns": base + 3, "fresh_read_end_ns": base + 4,
                    "complete_write_start_ns": base + 5, "write_end_ns": base + 6,
                    "partial_b64": base64.b64encode(partial).decode(), "partial_sha256": hashlib.sha256(partial).hexdigest(),
                    "held_b64": base64.b64encode(partial).decode(), "held_sha256": hashlib.sha256(partial).hexdigest(),
                    "fresh_b64": base64.b64encode(partial).decode(), "fresh_sha256": hashlib.sha256(partial).hexdigest(),
                    "completed_b64": base64.b64encode(expected).decode(), "completed_sha256": hashlib.sha256(expected).hexdigest()})
            previous = expected
        self.assertEqual(audit.audit_raw(raw, seed_raw, HERE), [])
        mutated = copy.deepcopy(raw)
        mutated["atomic_rows"][0]["fresh_b64"] = "eA=="
        self.assertTrue(audit.audit_raw(mutated, seed_raw, HERE))


if __name__ == "__main__":
    unittest.main()
