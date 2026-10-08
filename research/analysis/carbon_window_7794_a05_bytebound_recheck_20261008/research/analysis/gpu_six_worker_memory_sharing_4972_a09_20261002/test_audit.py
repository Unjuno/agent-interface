import unittest

import audit


def good_row(worker_id):
    initial = (audit.SEED % 997) + worker_id * 11
    checksum = audit.NUMEL * (initial + audit.OPS)
    return {
        "worker_id": worker_id,
        "pid": 1000 + worker_id,
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


def good_samples():
    return [
        {"memory_free_mib": "12000", "memory_used_mib": "4384", "utilization_gpu_pct": "0"},
        {"memory_free_mib": "9000", "memory_used_mib": "7384", "utilization_gpu_pct": "50"},
    ]


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
        self.assertTrue(any("5% allocator cap" in error for error in audit.audit_rows(rows)))

    def test_rejects_non_object_record(self):
        self.assertTrue(any("JSON object" in error for error in audit.audit_rows([None])))

    def test_accepts_bounded_host_gpu_samples(self):
        self.assertEqual(audit.audit_host_rows(good_samples()), [])

    def test_rejects_low_host_gpu_free_memory(self):
        samples = good_samples()
        samples[1]["memory_free_mib"] = "3000"
        self.assertTrue(any("fell below 4 GiB" in error for error in audit.audit_host_rows(samples)))

    def test_rejects_low_host_gpu_baseline(self):
        samples = good_samples()
        samples[0]["memory_free_mib"] = "9000"
        self.assertTrue(any("baseline free VRAM below 10 GiB" in error for error in audit.audit_host_rows(samples)))


if __name__ == "__main__":
    unittest.main()
