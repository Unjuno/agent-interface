import unittest

from audit_intervals import audit_overlap_rows


def fixture():
    replacements = [{"start_ns": i * 10, "end_ns": i * 10 + 1, "replace_index": i}
                    for i in range(4096)]
    reads = []
    for reader in ("reader-a", "reader-b"):
        for i in range(16):
            start = i * 10
            reads.append({"reader_id": reader, "reader_pid": 101 if reader == "reader-a" else 202,
                          "read_index": i,
                          "start_ns": start, "end_ns": start + 1})
    return reads, replacements


class IndependentAuditTests(unittest.TestCase):
    def test_fixture_audits_with_exact_denominators(self):
        reads, replacements = fixture()
        result = audit_overlap_rows(reads, replacements)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["overlap_count"], 32)

    def test_mutations_fail_closed(self):
        reads, replacements = fixture()
        controls = []
        controls.append((reads[:-1], replacements))
        controls.append((reads + [reads[0]], replacements))
        controls.append((reads, replacements[:-1]))
        duplicate_replace = [dict(row) for row in replacements]
        duplicate_replace[-1]["replace_index"] = 0
        controls.append((reads, duplicate_replace))
        bad_bool = [dict(row) for row in reads]
        bad_bool[0]["start_ns"] = True
        controls.append((bad_bool, replacements))
        same_pid = [dict(row, reader_pid=101) for row in reads]
        controls.append((same_pid, replacements))
        no_overlap = [dict(row, start_ns=50000 + i * 10, end_ns=50001 + i * 10)
                      for i, row in enumerate(reads)]
        controls.append((no_overlap, replacements))
        for changed_reads, changed_replacements in controls:
            with self.subTest(reads=len(changed_reads), replacements=len(changed_replacements)):
                self.assertTrue(audit_overlap_rows(changed_reads, changed_replacements)["errors"])


if __name__ == "__main__":
    unittest.main()
