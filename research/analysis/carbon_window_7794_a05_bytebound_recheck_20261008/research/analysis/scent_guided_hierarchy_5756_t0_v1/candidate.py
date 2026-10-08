"""Policies for a finite, no-model GUI-search method check (Issue #5756 T0)."""

import re

POLICIES = ("scent_backtrack", "exhaustive", "strongest_cue", "direct_search", "tree_search")


def _terms(task):
    return [word for word in re.findall(r"[a-z0-9]+", task.lower()) if len(word) > 2]


def _cue(edge, terms):
    words = re.findall(r"[a-z0-9]+", (edge["label"] + " " + edge.get("nearby", "")).lower())
    return sum(term in words for term in terms) + edge.get("saliency", 0) / 100


def _target(label, terms):
    words = set(re.findall(r"[a-z0-9]+", label.lower()))
    return bool(terms) and all(term in words for term in terms)


def run_policy(api, task, policy):
    """Use only current observations and opaque observe/navigate/backtrack calls.

    The API deliberately exposes no graph, transition table, hidden-screen labels,
    or target oracle. The independent harness owns those data.
    """
    if policy not in POLICIES:
        raise ValueError(f"unknown policy: {policy}")
    terms = _terms(task)
    trace = []
    seen = set()
    parent = {}
    queue = []
    claim = {"found": False, "screen_id": None}

    while api.budget_remaining() > 0:
        obs = api.observe()
        trace.append({"kind": "OBSERVE", "observation": obs})
        here = obs["screen_id"]
        claim["screen_id"] = here
        seen.add(here)
        if _target(obs["label"], terms):
            claim = {"found": True, "screen_id": here}
            break

        edges = obs["edges"]
        for edge in edges:
            if not edge["reversible"]:
                if api.budget_remaining() <= 0:
                    break
                receipt = api.refuse(edge["id"])
                trace.append(receipt)

        safe = [edge for edge in edges if edge["reversible"]]
        if api.budget_remaining() <= 0:
            break
        candidate = None
        if policy == "direct_search":
            candidate = next((edge for edge in safe if edge.get("kind") == "direct_search"), None)
        elif policy == "strongest_cue":
            tried = parent.get(here, {}).get("tried", set())
            candidate = max((edge for edge in safe if edge["id"] not in tried),
                            key=lambda edge: edge.get("saliency", 0), default=None)
        elif policy == "scent_backtrack":
            ordered = sorted(safe, key=lambda edge: (_cue(edge, terms), edge["id"]), reverse=True)
            candidate = next((edge for edge in ordered if edge["id"] not in parent.get(here, {}).get("tried", set())), None)
        elif policy == "tree_search":
            # Step-level breadth-first frontier: enqueue only currently observed,
            # safe edges; expand in stable display order, never unseen descendants.
            for edge in safe:
                key = (here, edge["id"])
                if key not in parent.get(here, {}).get("queued", set()):
                    parent.setdefault(here, {}).setdefault("queued", set()).add(key)
                    queue.append((here, edge))
            candidate = next((edge for node, edge in queue if node == here), None)
        else:  # deterministic exhaustive depth-first enumeration
            candidate = next((edge for edge in safe if edge["id"] not in parent.get(here, {}).get("tried", set())), None)

        if candidate is not None:
            receipt = api.navigate(candidate["id"])
            trace.append(receipt)
            parent.setdefault(here, {}).setdefault("tried", set()).add(candidate["id"])
            if receipt.get("kind") == "NAVIGATE":
                claim["screen_id"] = receipt["to_screen"]
                parent[receipt["to_screen"]] = {"parent": here, "edge_id": candidate["id"], "tried": set()}
                if policy == "tree_search":
                    queue = [(node, edge) for node, edge in queue if not (node == here and edge["id"] == candidate["id"])]
            continue

        if here in parent and "parent" in parent[here]:
            receipt = api.backtrack()
            trace.append(receipt)
            claim["screen_id"] = receipt["to_screen"]
            continue
        if policy == "tree_search" and queue:
            break
        break

    return {"policy": policy, "claim": claim, "trace": trace,
            "budget_remaining": api.budget_remaining()}

