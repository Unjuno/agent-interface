"""Postformal comparison helper; never invokes an experimental allocation.

Only a process-specific BytesIO address in one registered negative-control
exception may differ. All other JSON values and fields must agree exactly.
Original auditor/output bytes remain unchanged.
"""
from __future__ import annotations
import argparse
import copy
import json
import re
from pathlib import Path

PREFIX = "case-0:UNREADABLE:UnidentifiedImageError:cannot identify image file <_io.BytesIO object at "
ADDRESS = re.compile(re.escape(PREFIX) + r"0x[0-9a-fA-F]+>")

def compare(a: dict, b: dict) -> dict:
    left, right = copy.deepcopy(a), copy.deepcopy(b)
    changed = []
    for obj in (left, right):
        if obj.get("decision") != "PASS_INKSCAPE_PRESERVED_DOCUMENT_SCOPED":
            raise ValueError("Unexpected scientific decision")
        if obj.get("errors") != [] or obj.get("source_errors") != []:
            raise ValueError("Unresolved errors")
        controls = obj.get("corruption_controls", {})
        if len(controls) != 14 or not all(x.get("rejected") is True for x in controls.values()):
            raise ValueError("Corruption-control disagreement")
        message = controls["raster_missing"]["errors"][0]
        if not isinstance(message, str) or ADDRESS.fullmatch(message) is None:
            raise ValueError("Unexpected diagnostic shape")
        changed.append(message)
        controls["raster_missing"]["errors"][0] = PREFIX + "<process-address>>"
    if left != right:
        raise ValueError("Audit results differ outside the one permitted diagnostic address")
    return {"decision": "PASS_AUDIT_SEMANTIC_REPRODUCTION_SCOPED",
            "parsed_json_identical": a == b,
            "exception_address_differs": changed[0] != changed[1],
            "all_other_values_identical": True,
            "scope": "Only the explicitly identified BytesIO address was normalized; original files are unchanged."}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("retained", type=Path)
    parser.add_argument("recomputed", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(json.loads(args.retained.read_bytes()), json.loads(args.recomputed.read_bytes())), sort_keys=True, indent=2))
