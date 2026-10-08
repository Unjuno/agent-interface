"""Separate raw-only JSON pointer oracle; imports no runtime or matrix runner."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re


def decode(token):
    chars = []
    index = 0
    while index < len(token):
        char = token[index]
        if char == "~":
            index += 1
            if index == len(token) or token[index] not in "01":
                raise ValueError("escape")
            char = {"0": "~", "1": "/"}[token[index]]
        chars.append(char)
        index += 1
    return "".join(chars)


def resolve(root, pointer):
    if not pointer.startswith("/native_result/"):
        raise ValueError("scope")
    tokens = [decode(token) for token in pointer.split("/")[1:]]
    value = root
    for offset, token in enumerate(tokens):
        if type(value) is list:
            if not re.fullmatch(r"0|[1-9][0-9]*", token, flags=re.ASCII):
                raise ValueError("array token")
            key = int(token)
            if key >= len(value):
                raise ValueError("bounds")
        elif type(value) is dict and token in value:
            key = token
        else:
            raise ValueError("missing path")
        if offset == len(tokens) - 1:
            return value, key
        value = value[key]
    raise ValueError("empty pointer")


def expected(view):
    result = copy.deepcopy(view)
    refs = view["observation_references"]
    paths = refs if type(refs) is list else list(refs)
    try:
        changes = []
        for pointer in paths:
            if pointer == "/native_result/observation" or pointer.startswith("/native_result/observation/"):
                raise ValueError("canonical source")
            parent, key = resolve(result, pointer)
            if parent[key] != {"observation_ref": "/native_result/observation"}:
                raise ValueError("marker")
            changes.append((parent, key))
        for parent, key in changes:
            parent[key] = copy.deepcopy(view["native_result"]["observation"])
    except ValueError:
        return {"status": "exception", "exception": "ValueError"}
    for field in ("schema", "reference_scope", "observation_references"):
        result.pop(field)
    return {"status": "returned", "output": result}


def audit(raw, fixture_bytes, expected_source_hash):
    errors = []
    if raw.get("format") != "native-reference-boundary-v1":
        errors.append("format")
    if raw.get("source_sha256") != expected_source_hash:
        errors.append("source hash")
    if raw.get("fixture_sha256") != hashlib.sha256(fixture_bytes).hexdigest():
        errors.append("fixture hash")
    fixtures = json.loads(fixture_bytes)
    rows = raw.get("rows")
    if type(rows) is not list or len(rows) != len(fixtures):
        return {"errors": errors + ["row inventory"], "violations": None}
    violations = []
    for fixture, row in zip(fixtures, rows):
        if type(row) is not dict or row.get("id") != fixture["id"]:
            errors.append("row identity")
            continue
        wanted = expected(fixture["view"])
        required = {"id", "input_unchanged", *wanted}
        if set(row) != required or row.get("input_unchanged") is not True:
            violations.append(fixture["id"])
        elif any(row.get(key) != value for key, value in wanted.items()):
            violations.append(fixture["id"])
    return {"errors": errors, "violations": violations,
            "rows": len(rows), "valid_controls": sum(expected(f["view"])["status"] == "returned" for f in fixtures)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("fixtures", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    result = audit(json.loads(args.raw.read_bytes()), args.fixtures.read_bytes(),
                   hashlib.sha256(args.source.read_bytes()).hexdigest())
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["errors"] or (args.require_clean and result["violations"])))


if __name__ == "__main__":
    main()
