"""Check bounded-batch hover receipt composition against retained runtime evidence."""
import json
from pathlib import Path

from openttd_hover_receipt_batches_v1 import verify_batches


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-active-evidence-pair-01/2-stable-seed991004"


def refused(value):
    try:
        verify_batches(value, ROOT / "runtime")
    except ValueError:
        return True
    raise AssertionError("invalid batch evidence was accepted")


def main():
    result = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
    records = json.loads((ROOT / "calls.json").read_text(encoding="utf-8"))[5][
        "result"]["reply"]["records"]
    points = result["candidate_decision"]["points"]
    steps = result["hover_steps"]
    one = {"records": records[:], "steps": steps[:], "points": points[:]}
    ready = verify_batches([one], ROOT / "runtime")
    assert len(ready["receipts"]) == 3 and ready["batches"] == 1
    assert all([refused([]), refused([{"records": records, "steps": steps,
                                      "points": points},
                                     {"records": records, "steps": steps,
                                      "points": points}])])
    print({"receipts": len(ready["receipts"]), "batches": ready["batches"],
           "invalid_compositions_refused": 2})


if __name__ == "__main__":
    main()
