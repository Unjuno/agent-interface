"""Auditor contract tests over synthetic in-memory rows; no runner execution."""
import unittest

from audit import corruption_controls, validate


PHASES = {
    "atomic": [
        ("atomic_before_validation", 3788),
        ("atomic_candidate_ready_unpublished", 3788),
        ("atomic_after_publish", 3789),
        ("invalid_candidate_refused", 3789),
    ],
    "diagnostic": [
        ("diagnostic_before_write", 3788),
        ("diagnostic_partial_write", None),
        ("diagnostic_after_write", 3789),
    ],
}


def valid_raw():
    arms = []
    for arm_index, name in enumerate(("atomic", "diagnostic")):
        publisher = 1000 + arm_index
        pids = [1100 + arm_index * 10 + i for i in range(4)]
        rows = []
        serial = 0
        for phase, generation in PHASES[name]:
            for index, pid in enumerate(pids):
                serial += 1
                partial = phase == "diagnostic_partial_write"
                rows.append({
                    "phase": phase,
                    "request_id": f"{phase}-{serial:02d}",
                    "reader_index": index,
                    "pid": pid,
                    "bytes": 100 if not partial else 50,
                    "raw_sha256": "a" * 64,
                    "parse_ok": not partial,
                    "package_valid": not partial,
                    "generation": generation,
                    "embedded_digest": "b" * 64,
                })
        item = {"arm": name, "publisher_pid": publisher, "reader_pids": pids, "reader_exit_codes": [0] * 4, "observations": rows}
        if name == "atomic":
            item.update({
                "stale_proposal": {"generation": 3788, "active_generation": 3789, "disposition": "YIELD_STALE_GENERATION", "dispatch": False},
                "current_proposal": {"generation": 3789, "active_generation": 3789, "disposition": "ELIGIBLE_PROPOSAL_ONLY", "dispatch": False},
                "invalid_candidate_accepted": False,
                "active_before_invalid_sha256": "c" * 64,
                "active_after_invalid_sha256": "c" * 64,
            })
        else:
            item.update({"partial_invalid_reader_count": 4, "dispatch_count": 0})
        arms.append(item)
    return {
        "allocation": "needle-cross-process-publication-5045-v1",
        "issue": 5045,
        "formal_invocations": 1,
        "publisher_container_pid": 999,
        "input_git_blob": "45b80150dac503f4eb6f3cb5d82f9afa2c587107",
        "input_sha256": "d" * 64,
        "input_bytes": 15279,
        "candidate_sha256": "e" * 64,
        "reader_count_per_arm": 4,
        "query_count": 28,
        "dispatch_count": 0,
        "authority_granted": False,
        "arms": arms,
    }


class AuditContractTests(unittest.TestCase):
    def test_synthetic_complete_roster_satisfies_frozen_shape(self):
        self.assertEqual(validate(valid_raw()), [])

    def test_frozen_corruption_controls_reject(self):
        controls = corruption_controls(valid_raw())
        self.assertEqual(len(controls), 9)
        self.assertTrue(all(controls.values()), controls)


if __name__ == "__main__":
    unittest.main()

