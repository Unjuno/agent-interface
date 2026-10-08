"""Raw-only denominator/hash/decision audit; imports neither auditor nor candidate."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check(matrix):
    raw_bytes = (ROOT / "retained-raw.json").read_bytes()
    fixture_bytes = (ROOT / "fixtures.json").read_bytes()
    raw = json.loads(raw_bytes)
    errors = []
    expected = {}

    def visit(node, path):
        if type(node) is dict:
            for key in node:
                visit(node[key], path + (key,))
        elif type(node) is int:
            expected[(path, "float")] = float(node)
            if node == 0 or node == 1:
                expected[(path, "bool")] = bool(node)

    visit(raw, ())
    seen = set()
    for row in matrix["mutations"]:
        key = (tuple(row["path"]), row["replacement_type"])
        if key not in expected or key in seen:
            errors.append("denominator")
            continue
        seen.add(key)
        required = expected[key]
        if type(row["replacement"]) is not type(required) or row["replacement"] != required:
            errors.append("replacement_type_or_value")
        variant = copy.deepcopy(raw)
        node = variant
        for name in row["path"][:-1]:
            node = node[name]
        if type(row["original"]) is not int or row["original"] != node[row["path"][-1]]:
            errors.append("original_value")
        node[row["path"][-1]] = required
        encoded = json.dumps(variant, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if hashlib.sha256(encoded).hexdigest() != row["variant_sha256"]:
            errors.append("variant_hash")
        if row["legacy"]["status"] != "PASS_METHOD_SCOPED" or row["legacy"]["violations"]:
            errors.append("legacy_decision")
        if row["strict"]["status"] != "FAIL_RAW_AUDIT" or not row["strict"]["violations"]:
            errors.append("strict_decision")
    if seen != set(expected):
        errors.append("coverage")
    for name, data in (("original_raw_sha256", raw_bytes), ("fixture_sha256", fixture_bytes)):
        if matrix[name] != hashlib.sha256(data).hexdigest():
            errors.append("source_hash")
    for name in ("original_legacy", "original_strict"):
        if matrix[name]["status"] != "PASS_METHOD_SCOPED" or matrix[name]["violations"]:
            errors.append("unchanged_control")
    return {"status": "PASS_FINITE_TYPE_MATRIX" if not errors else "FAIL_MATRIX", "rows": len(seen), "errors": sorted(set(errors))}


def main():
    matrix = json.loads((ROOT / "matrix.json").read_bytes())
    result = check(matrix)
    controls = []
    for name in ("drop_row", "duplicate_row", "change_type", "change_hash", "false_pass"):
        altered = copy.deepcopy(matrix)
        if name == "drop_row":
            altered["mutations"].pop()
        elif name == "duplicate_row":
            altered["mutations"].append(altered["mutations"][0])
        elif name == "change_type":
            altered["mutations"][0]["replacement"] = altered["mutations"][0]["original"]
        elif name == "change_hash":
            altered["mutations"][0]["variant_sha256"] = "0" * 64
        else:
            altered["mutations"][0]["strict"]["status"] = "PASS_METHOD_SCOPED"
        outcome = check(altered)
        controls.append({"name": name, "audit": outcome})
    result["corruption_controls"] = controls
    passed = result["status"] == "PASS_FINITE_TYPE_MATRIX" and all(c["audit"]["status"] == "FAIL_MATRIX" for c in controls)
    with (ROOT / "matrix-audit.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
