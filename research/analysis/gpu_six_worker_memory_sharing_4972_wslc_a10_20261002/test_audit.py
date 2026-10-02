import unittest

import audit


def good_row(worker_id):
    initial = (audit.SEED % 997) + worker_id * 11
    checksum = audit.NUMEL * (initial + audit.OPS)
    return {
        "worker_id": worker_id,
        "pid": 2000 + worker_id,
        "seed": audit.SEED,
        "status": "ok",
        "device": audit.EXPECTED_DEVICE,
        "device_total_bytes": 16 * 1024**3,
        "global_free_before_bytes": 12 * 1024**3,
        "global_free_overlap_bytes": 8 * 1024**3,
        "global_free_after_bytes": 8 * 1024**3,
        "allocated_bytes": audit.WORKING_BYTES,
        "peak_allocated_bytes": audit.WORKING_BYTES,
        "numel": audit.NUMEL,
        "ops": audit.OPS,
        "initial_value": initial,
        "checksum": checksum,
        "expected_checksum": checksum,
    }


def good_samples():
    return [
        {"timestamp": "2026/10/02 00:00:00.000", "utilization_gpu_pct": "0", "memory_used_mib": "4000", "memory_free_mib": "12000"},
        {"timestamp": "2026/10/02 00:00:01.000", "utilization_gpu_pct": "50", "memory_used_mib": "8000", "memory_free_mib": "8000"},
    ]


class AuditContractTests(unittest.TestCase):
    def test_accepts_six_reconstructable_workers(self):
        self.assertEqual(audit.audit_rows([good_row(i) for i in range(6)]), [])

    def test_rejects_duplicate_worker_id(self):
        rows = [good_row(i) for i in range(6)]
        rows[-1]["worker_id"] = rows[0]["worker_id"]
        self.assertTrue(any("worker IDs" in error for error in audit.audit_rows(rows)))

    def test_rejects_wrong_checksum(self):
        rows = [good_row(i) for i in range(6)]
        rows[2]["checksum"] += 1
        self.assertTrue(any("checksum" in error for error in audit.audit_rows(rows)))

    def test_rejects_low_worker_global_free_memory(self):
        rows = [good_row(i) for i in range(6)]
        rows[0]["global_free_overlap_bytes"] = audit.MIN_GLOBAL_FREE - 1
        self.assertTrue(any("below 4 GiB" in error for error in audit.audit_rows(rows)))

    def test_rejects_allocator_overrun(self):
        rows = [good_row(i) for i in range(6)]
        rows[1]["peak_allocated_bytes"] = int(rows[1]["device_total_bytes"] * 0.05) + 1
        self.assertTrue(any("5% per-process cap" in error for error in audit.audit_rows(rows)))

    def test_accepts_bounded_host_gpu_samples(self):
        self.assertEqual(audit.audit_host_rows(good_samples()), [])

    def test_rejects_low_host_baseline(self):
        samples = good_samples()
        samples[0]["memory_free_mib"] = "9000"
        self.assertTrue(any("baseline" in error for error in audit.audit_host_rows(samples)))

    def test_rejects_low_host_reserve(self):
        samples = good_samples()
        samples[-1]["memory_free_mib"] = "3000"
        self.assertTrue(any("fell below 4 GiB" in error for error in audit.audit_host_rows(samples)))

    def test_four_frozen_mutations_are_rejected(self):
        mutations = audit.mutation_controls([good_row(i) for i in range(6)], good_samples())
        self.assertEqual(len(mutations), 4)
        self.assertTrue(all(item["rejected"] for item in mutations), mutations)


if __name__ == "__main__":
    unittest.main()
