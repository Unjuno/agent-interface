import copy
import json
import os
import unittest
from pathlib import Path

from audit import analyze, read_observer

DATA = Path(os.environ["R133_AUDIT_INPUTS"])
EVENTS = [json.loads(x) for x in (DATA / "events.jsonl").read_text().splitlines()]
OBSERVER = read_observer((DATA / "game-stderr.txt").read_bytes())
POSTHOC = json.loads((DATA / "posthoc-audit.json").read_text())


class CorruptionControls(unittest.TestCase):
    def check_rejected(self, events, observer=None, posthoc=None):
        with self.assertRaises(ValueError):
            analyze(events, observer if observer is not None else OBSERVER,
                    posthoc if posthoc is not None else POSTHOC)

    def test_01_dropped_raw_event(self):
        self.check_rejected(EVENTS[:-1])

    def test_02_fabricated_button_up(self):
        rows = copy.deepcopy(EVENTS)
        row = next(r for r in rows if r.get("event") == "pointer_admission"
                   and r.get("operation") == "button_down")
        row["operation"] = "button_up"
        self.check_rejected(rows)

    def test_03_wrong_terminal_identity(self):
        rows = copy.deepcopy(EVENTS)
        terminal = next(r for r in rows if r.get("event") == "terminal"
                        and r.get("id") == next(d["id"] for d in EVENTS
                          if d.get("event") == "pointer_admission"
                          and d.get("operation") == "button_down"))
        terminal["id"] = "wrong-id"
        self.check_rejected(rows)

    def test_04_unverified_release(self):
        rows = copy.deepcopy(EVENTS)
        terminal = next(r for r in rows if r.get("event") == "terminal"
                        and r.get("id") == next(d["id"] for d in EVENTS
                          if d.get("event") == "pointer_admission"
                          and d.get("operation") == "button_down"))
        terminal["release"]["verified"] = False
        self.check_rejected(rows)

    def test_05_non_neutral_release(self):
        rows = copy.deepcopy(EVENTS)
        terminal = next(r for r in rows if r.get("event") == "terminal"
                        and r.get("id") == next(d["id"] for d in EVENTS
                          if d.get("event") == "pointer_admission"
                          and d.get("operation") == "button_down"))
        terminal["release"]["buttons_down"] = ["left"]
        self.check_rejected(rows)


if __name__ == "__main__":
    unittest.main()

