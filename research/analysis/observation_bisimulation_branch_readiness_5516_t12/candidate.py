"""Frozen finite LTS candidate for Issue #5516 T12; emits one JSONL row/case."""

import json


CASES = {
    "positive_control": {
        "left": {"s": {"OPEN": ["after_open"]}, "after_open": {"SAVE": ["done"]}, "done": {}},
        "right": {"t": {"OPEN": ["after_open"]}, "after_open": {"SAVE": ["done"]}, "done": {}},
        "initial_left": "s",
        "initial_right": "t",
    },
    "branch_readiness_split": {
        "left": {
            "s": {"OPEN": ["copy_branch", "delete_branch"]},
            "copy_branch": {"SAVE": ["done"], "COPY": ["done"]},
            "delete_branch": {"SAVE": ["done"], "DELETE": ["done"]},
            "done": {},
        },
        "right": {
            "t": {"OPEN": ["combined_branch"]},
            "combined_branch": {"SAVE": ["done"], "COPY": ["done"], "DELETE": ["done"]},
            "done": {},
        },
        "initial_left": "s",
        "initial_right": "t",
    },
    "visible_label_mismatch": {
        "left": {
            "s": {"OPEN": ["copy_branch", "delete_branch"]},
            "copy_branch": {"SAVE": ["done"], "COPY": ["done"]},
            "delete_branch": {"SAVE": ["done"], "DELETE": ["done"]},
            "done": {},
        },
        "right": {
            "t": {"OPEN": ["combined_branch"]},
            "combined_branch": {"SAVE": ["done"], "COPY": ["done"], "ARCHIVE": ["done"]},
            "done": {},
        },
        "initial_left": "s",
        "initial_right": "t",
    },
}


def traces(graph, initial):
    result = {()}
    frontier = {(initial, ())}
    visited = set()
    while frontier:
        state, prefix = frontier.pop()
        if (state, prefix) in visited:
            continue
        visited.add((state, prefix))
        for label, targets in graph[state].items():
            for target in targets:
                word = prefix + (label,)
                result.add(word)
                frontier.add((target, word))
    return sorted([list(word) for word in result])


def bisimilar(left, right, initial_left, initial_right):
    pairs = {(a, b) for a in left for b in right}
    changed = True
    while changed:
        changed = False
        for a, b in tuple(pairs):
            la, rb = left[a], right[b]
            left_ok = all(
                label in rb and all(any((ta, tb) in pairs for tb in rb[label]) for ta in targets)
                for label, targets in la.items()
            )
            right_ok = all(
                label in la and all(any((ta, tb) in pairs for ta in la[label]) for tb in targets)
                for label, targets in rb.items()
            )
            if not left_ok or not right_ok:
                pairs.remove((a, b))
                changed = True
    return (initial_left, initial_right) in pairs


def run():
    for case_id, case in CASES.items():
        lt = traces(case["left"], case["initial_left"])
        rt = traces(case["right"], case["initial_right"])
        yield {
            "case_id": case_id,
            "left": case["left"],
            "right": case["right"],
            "initial_left": case["initial_left"],
            "initial_right": case["initial_right"],
            "left_traces": lt,
            "right_traces": rt,
            "trace_equal": lt == rt,
            "bisimilar": bisimilar(case["left"], case["right"], case["initial_left"], case["initial_right"]),
        }


if __name__ == "__main__":
    for item in run():
        print(json.dumps(item, sort_keys=True, separators=(",", ":")))
