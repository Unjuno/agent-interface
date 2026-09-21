"""Construction controls and semantic corruption tests; no live input or reruns."""
import copy
import json
from pathlib import Path
import sys
import unittest
from audit import verify_row

ROOT = Path(__file__).resolve().parent
CONSTRUCTION = ROOT / "construction-02"


def cases():
    return [json.loads(p.read_text()) for p in sorted(CONSTRUCTION.glob("case-*/row.json"))]


def controls(row):
    def change(name, fn):
        altered = copy.deepcopy(row)
        fn(altered)
        verdict = verify_row(altered, row["letter"])
        return name, bool(verdict["errors"] or verdict["gate_failures"])

    variants = [
        ("nonzero_exit", lambda r: r.update(receiver_exit=1)),
        ("foreign_actor", lambda r: r.update(receiver_pid=r["receiver_pid"]+1)),
        ("missing_native", lambda r: r["native"].clear()),
        ("changed_keymap", lambda r: r["commands"][0]["post"]["keymap"].__setitem__(r["keycode"]//8, 0)),
        ("changed_command", lambda r: r["commands"][0].update(kind="up")),
        ("wrong_focus", lambda r: r["terminal"].update(focus=0)),
        ("missing_final", lambda r: r["events"].pop()),
        ("wrong_repeat", lambda r: r["repeat_readback"].update(global_mode=7)),
        ("wrong_barrier", lambda r: r["barrier"].update(token=0)),
        ("reversed_clock", lambda r: r.update(end_ns=r["start_ns"]-1)),
        ("wrong_effect", lambda r: r["events"][-1].update(value="incorrect")),
        ("nonneutral_button", lambda r: r["terminal"].update(buttons=256)),
    ]
    output = {}
    for name, fn in variants:
        # Update redundant stdout too: the check must reach semantic validation.
        def semantic_mutation(r, fn=fn):
            fn(r)
            r["receiver_stdout"] = "".join(json.dumps(e, sort_keys=True)+"\n" for e in r["events"])
        label, rejected = change(name, semantic_mutation)
        output[label] = rejected
    return output


class Contract(unittest.TestCase):
    def test_construction_positives(self):
        rows = cases()
        self.assertEqual(len(rows), 10)
        for row in rows:
            with self.subTest(index=row["index"]):
                result = verify_row(row, "c")
                self.assertEqual(result["errors"], [])
                self.assertEqual(result["gate_failures"], [])

    def test_twelve_semantic_negatives(self):
        negative = controls(cases()[1])
        self.assertEqual(len(negative), 12)
        self.assertTrue(all(negative.values()), negative)

    def test_empty_schema_refuses(self):
        self.assertTrue(verify_row({})["errors"])

    def test_extra_down_refuses(self):
        row = copy.deepcopy(cases()[1])
        row["commands"].append(copy.deepcopy(row["commands"][0]))
        self.assertTrue(verify_row(row, "c")["errors"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--formal":
        row = json.loads(Path(sys.argv[2]).read_text())
        result = controls(row)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if len(result)==12 and all(result.values()) else 1)
    unittest.main()
