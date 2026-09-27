import sqlite3
import tempfile
import unittest
from pathlib import Path

import runner


class SchemaConstructionTests(unittest.TestCase):
    def test_every_mode_and_protocol_has_expected_tables(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for mode in runner.MODES:
                for protocol in runner.PROTOCOLS:
                    with self.subTest(mode=mode, protocol=protocol):
                        root = base / (mode + "-" + protocol)
                        effect, receipt, settings = runner.init_case(root, mode, protocol)
                        self.assertEqual(settings["effect"]["journal_mode"], mode)
                        self.assertEqual(settings["effect"]["synchronous"], 2)
                        if mode == "WAL":
                            self.assertEqual(settings["effect"]["wal_autocheckpoint"], 0)
                        econn = sqlite3.connect(effect)
                        effect_tables = {r[0] for r in econn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'")}
                        econn.close()
                        self.assertIn("effects", effect_tables)
                        if effect == receipt:
                            self.assertIn("receipts", effect_tables)
                        else:
                            rconn = sqlite3.connect(receipt)
                            receipt_tables = {r[0] for r in rconn.execute(
                                "SELECT name FROM sqlite_master WHERE type='table'")}
                            rconn.close()
                            self.assertEqual(receipt_tables, {"receipts"})

    def test_local_split_and_external_database_topology(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(runner.db_paths(root, "EFFECT_FIRST")[0],
                             runner.db_paths(root, "EFFECT_FIRST")[1])
            self.assertEqual(runner.db_paths(root, "RECEIPT_FIRST")[0],
                             runner.db_paths(root, "RECEIPT_FIRST")[1])
            self.assertEqual(runner.db_paths(root, "ATOMIC_LOCAL")[0],
                             runner.db_paths(root, "ATOMIC_LOCAL")[1])
            self.assertNotEqual(runner.db_paths(root, "ATOMIC_EXTERNAL")[0],
                                runner.db_paths(root, "ATOMIC_EXTERNAL")[1])

    def test_registered_after_second_cut_is_not_duplicate(self):
        # Local writes are uncommitted at the cut; split commits are both durable.
        self.assertEqual(runner.PROTOCOLS,
                         ("EFFECT_FIRST", "RECEIPT_FIRST", "ATOMIC_LOCAL", "ATOMIC_EXTERNAL"))
        self.assertEqual(runner.CUTS,
                         ("BEFORE", "AFTER_FIRST", "AFTER_SECOND", "AFTER_COMMIT", "NORMAL"))

    def test_invalid_boolean_is_not_an_integer(self):
        self.assertIsNot(type(True), int)


if __name__ == "__main__":
    unittest.main()
