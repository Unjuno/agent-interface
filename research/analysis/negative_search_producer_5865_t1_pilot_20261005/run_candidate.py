import json
from pathlib import Path

from inventory_producer import certify_from_pages


ROOT = Path(__file__).resolve().parent
source = json.loads((ROOT / "candidate_input.json").read_text())
results = []
for case in source["cases"]:
    surface = case.get("surface_ids", ["app-A"])[0]
    page = {
        "schema": "inventory.v1",
        "surface_id": surface,
        "epoch": case["epoch"],
        "page_index": 0,
        "page_count": 1,
        "universe_complete": case.get("producer_complete", False),
        "writer_coverage": case.get("writer_coverage", True),
        "predicate_version": "text-exact.v1",
        "items": case["items"],
    }
    if "page_epochs" in case and len(set(case["page_epochs"])) > 1:
        page["epoch"] = case["page_epochs"][1]
    results.append({"case_id": case["case_id"],
                    "candidate": certify_from_pages([page], source["query"])})

out = {"allocation": source["allocation"], "case_count": len(results), "results": results}
(ROOT / "candidate_output.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({"allocation": out["allocation"], "case_count": out["case_count"]}))
