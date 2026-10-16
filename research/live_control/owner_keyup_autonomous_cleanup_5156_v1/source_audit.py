"""Static callsite classification for the exact pinned v10/v3 checkout."""

from __future__ import annotations

import ast
from pathlib import Path


EXPECTED_RELEASE_LINES = {
    205: "owner_stop",
    219: "owner_lease_cleanup",  # expiry, cancel, surface/focus invalidation
    261: "queued_explicit_release_or_close",
    356: "conditional_thread_finalizer",
}


class ReleaseCallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.lines: list[int] = []

    def visit_FunctionDef(self, node):
        if node.name == "_run":
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "release":
                    self.lines.append(child.lineno)


def classify(owner_path: Path, wrapper_path: Path) -> dict:
    owner_text = owner_path.read_text(encoding="utf-8")
    owner_tree = ast.parse(owner_text)
    visitor = ReleaseCallVisitor()
    visitor.visit(owner_tree)
    actual = sorted(visitor.lines)
    expected = sorted(EXPECTED_RELEASE_LINES)
    wrapper_text = wrapper_path.read_text(encoding="utf-8")
    checks = {
        "release_callsites_exact": actual == expected,
        "caller_wrapper_has_explicit_up_bracket": 'operation not in ("up", "button_up")' in wrapper_text,
        "caller_wrapper_has_release_close_bracket": 'operation in ("release", "close")' in wrapper_text,
        "owner_call_queues_requests": "self.requests.put((operation, lease, key, done, reply))" in owner_text,
    }
    return {
        "callsites": [{"line": line, "class": EXPECTED_RELEASE_LINES.get(line, "unclassified")} for line in actual],
        "checks": checks,
        "ok": all(checks.values()),
    }


if __name__ == "__main__":
    import json
    import sys
    result = classify(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(not result["ok"])
