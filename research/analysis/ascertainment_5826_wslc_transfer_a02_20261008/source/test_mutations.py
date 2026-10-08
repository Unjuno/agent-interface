"""Read-only auditor corruption controls; the candidate is never rerun."""
import copy
import json
import sys
from pathlib import Path

import audit_result


def main(candidate_path):
    root = Path(__file__).resolve().parent
    fixture_path, oracle_path = root / "fixture.json", root / "ORACLE.json"
    base = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    controls = []

    item = copy.deepcopy(base); item["records"].pop(); controls.append(("omitted-row", item, fixture, oracle))
    item = copy.deepcopy(base); item["records"].append(copy.deepcopy(item["records"][0])); controls.append(("duplicate-row", item, fixture, oracle))
    item = copy.deepcopy(base); next(r for r in item["records"] if r["opportunity_id"] == "F03" and r["channel"] == "post_effect_audit")["link_key"] = "opportunity:F04"; controls.append(("mislinked-event", item, fixture, oracle))
    item = copy.deepcopy(base); row = next(r for r in item["records"] if r["opportunity_id"] == "N18" and r["channel"] == "verifier"); row.update(status="not_detected", unknown_reason=None); controls.append(("unknown-as-negative", item, fixture, oracle))
    truth = copy.deepcopy(oracle); row = next(r for r in truth["opportunities"] if r["id"] == "F02"); row.update(has_fault=False, fault_class=None, severity=None); controls.append(("oracle-truth-flip", base, fixture, truth))

    for name, data, fixture_data, oracle_data in controls:
        try:
            audit_result.audit(data, fixture_data, oracle_data,
                               fixture_path=fixture_path, oracle_path=oracle_path)
        except (ValueError, KeyError, TypeError):
            continue
        raise AssertionError(f"auditor accepted mutation: {name}")
    print(f"PASS: rejected {len(controls)}/{len(controls)} mutations: " +
          ", ".join(name for name, *_ in controls))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_mutations.py candidate.json")
    main(sys.argv[1])
