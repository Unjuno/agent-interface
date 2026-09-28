#!/usr/bin/env python3
"""Source-only audit of Issue #5156's pinned InputOwner release call graph.

Uses Python's standard-library AST only. It does not import runtime modules or
execute X11, model, container, GPU, or input behavior.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "owner": "ec4d6969d4c0cae2ee0a2989455a2fe87f930d90aeb3451afd3450c7c85e9718",
    "wrapper": "5ffdbb3679451fefdc3836917d43d924f0f43c8082d21327207ecefbd87f5be6",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_function(root: ast.AST, cls_name: str, fn_name: str) -> ast.FunctionDef:
    cls = next(n for n in root.body if isinstance(n, ast.ClassDef) and n.name == cls_name)
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == fn_name)


def audit(owner_path: Path, wrapper_path: Path) -> dict[str, object]:
    owner_bytes = owner_path.read_bytes()
    wrapper_bytes = wrapper_path.read_bytes()
    owner_hash = sha256(owner_bytes)
    wrapper_hash = sha256(wrapper_bytes)
    if owner_hash != EXPECTED["owner"] or wrapper_hash != EXPECTED["wrapper"]:
        raise SystemExit(
            f"STOP_SOURCE_HASH_MISMATCH owner={owner_hash} wrapper={wrapper_hash}"
        )

    owner_text = owner_bytes.decode("utf-8-sig")
    wrapper_text = wrapper_bytes.decode("utf-8-sig")
    run = find_function(ast.parse(owner_text), "InputOwner", "_run")
    parent = {child: node for node in ast.walk(run) for child in ast.iter_child_nodes(node)}

    release_calls: list[dict[str, object]] = []
    for node in ast.walk(run):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "release"
        ):
            continue
        reason = ast.unparse(node.args[0]) if node.args else ""
        if reason in {"'stop_requested'", "'thread_exit'"}:
            kind = "autonomous"
        elif reason == "op":
            kind = "queued_explicit_or_close"
        elif "expired" in reason and "cancelled" in reason:
            kind = "autonomous_expiry_cancel_focus_surface"
        else:
            kind = "unclassified"
        release_calls.append({"line": node.lineno, "reason": reason, "kind": kind})

    wrapper_call = find_function(
        ast.parse(wrapper_text), "InputOwner", "call"
    )
    inner_calls = [
        node for node in ast.walk(wrapper_call)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "call"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "_inner"
    ]
    if len(release_calls) != 4 or any(x["kind"] == "unclassified" for x in release_calls):
        raise SystemExit(f"STOP_UNCLASSIFIED_RELEASE_CALLGRAPH {release_calls}")
    if len(inner_calls) != 2:
        raise SystemExit(f"STOP_UNEXPECTED_WRAPPER_DELEGATIONS {len(inner_calls)}")

    autonomous = [x for x in release_calls if x["kind"].startswith("autonomous")]
    if len(autonomous) != 3:
        raise SystemExit(f"FAIL_NO_AUTONOMOUS_RELEASE_OUTSIDE_CALLER_BRACKET {release_calls}")

    return {
        "status": "PASS_AUTOMATIC_RELEASE_OUTSIDE_CALLER_BRACKET",
        "owner_sha256": owner_hash,
        "wrapper_sha256": wrapper_hash,
        "release_calls": sorted(release_calls, key=lambda x: int(x["line"])),
        "wrapper_inner_delegation_count": len(inner_calls),
        "autonomous_release_count": len(autonomous),
        "scope": "pinned source/control-flow only; no runtime or X11 behavior",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-source", type=Path, required=True)
    parser.add_argument("--wrapper-source", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.owner_source, args.wrapper_source), indent=2))
