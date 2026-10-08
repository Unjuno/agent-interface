"""Run the frozen finite candidate cases once and emit deterministic JSON."""

import json

from detector import decide


with open("cases.json", encoding="utf-8") as stream:
    payload = json.load(stream)

results = []
for case in payload["cases"]:
    result = decide(
        case["witnesses"],
        current_generation=payload["current_generation"],
        independence_depth=payload["independence_depth"],
        required_domains=payload["required_domains"],
    )
    result["case_id"] = case["case_id"]
    results.append(result)

print(json.dumps({"results": results}, indent=2, sort_keys=True))
