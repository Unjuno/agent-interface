"""Auditor mutation controls; no candidate or GUI input is executed here."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from auditor import audit
from candidate import build


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    design = json.loads((root / "design.json").read_text())
    truth = json.loads((root / "scorer_fixture.json").read_text())
    original = json.loads(args.raw.read_text())
    mutations = {}

    leak = copy.deepcopy(original)
    leak["arms"]["interleaved"]["schedule"][0] = "heldout_delta"
    leak["arms"]["interleaved"]["effects"][0]["variant"] = "heldout_delta"
    mutations["heldout_leak"] = leak

    omitted = copy.deepcopy(original)
    omitted["arms"]["blocked"]["schedule"].pop()
    omitted["arms"]["blocked"]["effects"].pop()
    mutations["omitted_attempt"] = omitted

    duplicate = copy.deepcopy(original)
    duplicate["arms"]["blocked"]["schedule"][-1] = duplicate["arms"]["blocked"]["schedule"][0]
    mutations["duplicated_variant_attempt"] = duplicate

    false_effect = copy.deepcopy(original)
    false_effect["arms"]["blocked"]["effects"][0]["observed_forward_effect"]["value"] = False
    mutations["false_forward_effect"] = false_effect

    broken_inverse = copy.deepcopy(original)
    broken_inverse["arms"]["interleaved"]["effects"][0]["observed_inverse_effect"]["value"] = True
    mutations["failed_inverse"] = broken_inverse

    initial = audit(design, truth, original)
    rejected = {
        name: audit(design, truth, mutated)["decision"] == "FAIL"
        for name, mutated in mutations.items()
    }
    rebuilt = build(design)
    reproduced = rebuilt == original
    status = "PASS" if initial["decision"] == "METHOD_PASS_SCOPED" and all(rejected.values()) and reproduced else "FAIL"
    print(json.dumps({"initial": initial["decision"], "mutations_rejected": rejected,
                      "candidate_reproduced": reproduced, "status": status}, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
