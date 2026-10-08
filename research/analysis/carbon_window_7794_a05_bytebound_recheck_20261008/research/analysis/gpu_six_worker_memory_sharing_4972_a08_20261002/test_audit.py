import sys
import unittest

import audit


def good_row(worker_id):
    initial = (audit.SEED % 997) + worker_id * 11
    checksum = audit.NUMEL * (initial + audit.OPS)
    return {
        "worker_id": worker_id,
        "seed": audit.SEED,
        "status": "ok",
        "device": audit.EXPECTED_DEVICE,
        "numel": audit.NUMEL,
        "ops": audit.OPS,
        "allocated_bytes": audit.WORKING_BYTES,
        "peak_allocated_bytes": audit.WORKING_BYTES,
        "device_total_bytes": 16 * 1024**3,
        "global_free_overlap_bytes": 8 * 1024**3,
        "initial_value": initial,
        "checksum": checksum,
        "expected_checksum": checksum,
    }


class AuditContractTests(unittest.TestCase):
    def test_accepts_six_reconstructable_workers(self):
        self.assertEqual(audit.audit_rows([good_row(i) for i in range(6)]), [])

    def test_rejects_missing_duplicate_worker(self):
        rows = [good_row(i) for i in range(5)] + [good_row(4)]
        self.assertTrue(any("worker IDs" in error for error in audit.audit_rows(rows)))

    def test_rejects_wrong_checksum(self):
        rows = [good_row(i) for i in range(6)]
        rows[2]["checksum"] += 1
        self.assertTrue(any("checksum" in error for error in audit.audit_rows(rows)))

    def test_rejects_low_global_free_memory(self):
        rows = [good_row(i) for i in range(6)]
        rows[0]["global_free_overlap_bytes"] = audit.MIN_GLOBAL_FREE - 1
        self.assertTrue(any("below 4 GiB" in error for error in audit.audit_rows(rows)))

    def test_rejects_allocator_overrun(self):
        rows = [good_row(i) for i in range(6)]
        rows[1]["peak_allocated_bytes"] = int(rows[1]["device_total_bytes"] * 0.05) + 1
        self.assertTrue(any("allocator peak" in error for error in audit.audit_rows(rows)))


if __name__ == "__main__":
    unittest.main()
