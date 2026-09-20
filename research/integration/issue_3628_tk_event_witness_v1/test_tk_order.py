from __future__ import annotations

import json
import os
import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from audit import audit_row
from fixture import configure_fixture


class TkBindtagOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.name == "nt":
            raise unittest.SkipTest("run Tk event construction under Linux/Xvfb")

    def test_fixture_passively_records_chord_before_save_effect(self) -> None:
        root = tk.Tk()
        self.addCleanup(root.destroy)
        with tempfile.TemporaryDirectory(prefix="issue3628-tk-") as temp_dir:
            root_path = Path(temp_dir)
            effect_path = root_path / "effect.json"
            events_path = root_path / "events.jsonl"
            entry = configure_fixture(root, effect_path, events_path)
            root.update_idletasks()
            root.update()
            entry.focus_force()
            root.update()
            entry.insert(0, "marker-123")
            entry.event_generate("<KeyPress>", keysym="Control_L")
            entry.event_generate("<KeyPress>", keysym="s", state=0x4)
            root.update()

            meta_tags = list(entry.bindtags())
            tag = "AgentInterfacePassiveKeyWitness"
            self.assertLess(meta_tags.index(tag), meta_tags.index(entry.winfo_class()))
            events = [json.loads(line) for line in events_path.read_text().splitlines()]
            effect = json.loads(effect_path.read_text())
            result = audit_row(events, effect, "marker-123")
            self.assertTrue(result["pass"], result)
            self.assertEqual(result["control_keypresses"], 1)
            self.assertEqual(result["control_s_keypresses"], 1)


if __name__ == "__main__":
    unittest.main()
