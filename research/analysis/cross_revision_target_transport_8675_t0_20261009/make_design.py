"""Create the deterministic synthetic corpus frozen for Issue #8675 T0."""

from __future__ import annotations

import json
import random
import sys


def node(node_id, role, label, actionable, path):
    return {"id": node_id, "role": role, "label": label,
            "actionable": actionable, "path": path}


def base_graph(seed, revision, symmetric=False):
    prefix = "src" if revision == "source" else "cur"
    drafts_label = "Data" if symmetric else "Drafts"
    profile_label = "Data" if symmetric else "Profile"
    ids = {key: f"{prefix}-{seed}-{key}" for key in ("root", "drafts", "target", "profile", "other")}
    paths = {"root": "rev0/0", "drafts": "rev0/0/0", "target": "rev0/0/0/0",
             "profile": "rev0/0/1", "other": "rev0/0/1/0"}
    if revision == "current":
        paths = {key: value.replace("rev0", "rev1") for key, value in paths.items()}
    rows = [
        node(ids["root"], "window", "App", False, paths["root"]),
        node(ids["drafts"], "group", drafts_label, False, paths["drafts"]),
        node(ids["target"], "button", "Save", True, paths["target"]),
        node(ids["profile"], "group", profile_label, False, paths["profile"]),
        node(ids["other"], "button", "Save", True, paths["other"]),
    ]
    edges = [[ids["root"], ids["drafts"]], [ids["drafts"], ids["target"]],
             [ids["root"], ids["profile"]], [ids["profile"], ids["other"]]]
    return {"nodes": rows, "edges": edges, "root_id": ids["root"]}, ids


def relabel_current(seed, mode, symmetric=False):
    """Create a current revision with the same observable semantics and new identity/path."""
    labels = {"root": ("window", "App", False),
              "drafts": ("group", "Data" if symmetric else "Drafts", False),
              "target": ("button", "Save", True),
              "profile": ("group", "Data" if symmetric else "Profile", False),
              "other": ("button", "Save", True)}
    ids = {key: f"cur-{seed}-{key}" for key in labels}
    order = ["root", "drafts", "target", "profile", "other"]
    paths = {"root": "rev1/0", "drafts": "rev1/0/0", "target": "rev1/0/0/0",
             "profile": "rev1/0/1", "other": "rev1/0/1/0"}
    edges = [["root", "drafts"], ["drafts", "target"], ["root", "profile"], ["profile", "other"]]
    key_to_id = dict(ids)
    if mode == "sibling_reorder":
        paths.update({"profile": "rev1/0/0", "other": "rev1/0/0/0",
                      "drafts": "rev1/0/1", "target": "rev1/0/1/0"})
        edges = [["root", "profile"], ["profile", "other"], ["root", "drafts"], ["drafts", "target"]]
        order = ["root", "profile", "other", "drafts", "target"]
    elif mode == "insert_duplicate_save":
        labels["archive"] = ("group", "Archive", False)
        labels["archive_save"] = ("button", "Save", True)
        key_to_id.update({"archive": f"cur-{seed}-archive", "archive_save": f"cur-{seed}-archive-save"})
        paths.update({"archive": "rev1/0/2", "archive_save": "rev1/0/2/0"})
        edges.extend([["root", "archive"], ["archive", "archive_save"]])
        order.extend(["archive", "archive_save"])
    elif mode == "transparent_wrapper":
        labels["wrapper"] = ("container", "Panel", False)
        key_to_id["wrapper"] = f"cur-{seed}-wrapper"
        paths.update({"wrapper": "rev1/0/0", "drafts": "rev1/0/0/0",
                      "target": "rev1/0/0/0/0", "profile": "rev1/0/1", "other": "rev1/0/1/0"})
        edges = [["root", "wrapper"], ["wrapper", "drafts"], ["drafts", "target"],
                 ["root", "profile"], ["profile", "other"]]
        order = ["root", "wrapper", "drafts", "target", "profile", "other"]
    rows = [node(key_to_id[k], *labels[k], paths[k]) for k in order]
    return {"nodes": rows, "edges": [[key_to_id[a], key_to_id[b]] for a, b in edges],
            "root_id": key_to_id["root"]}, key_to_id


def mutate_negative(seed, kind):
    source, source_ids = base_graph(seed, "source", symmetric=(kind == "automorphism"))
    current, current_ids = relabel_current(seed, "sibling_reorder", symmetric=(kind == "automorphism"))
    if kind == "removed_target":
        for row in current["nodes"]:
            if row["id"] in {current_ids["target"], current_ids["other"]}:
                row["label"] = "Open"
    elif kind == "semantic_role_change":
        for row in current["nodes"]:
            if row["id"] in {current_ids["target"], current_ids["other"]}:
                row["role"] = "textbox"
                row["actionable"] = False
    elif kind != "automorphism":
        raise ValueError(kind)
    return source, current, source_ids["target"], None


def case(case_id, split, family, seed, source, current, source_target, truth):
    return {"case_id": case_id, "split": split, "family": family, "seed": seed,
            "input": {"source_graph": source, "current_graph": current,
                      "source_target_id": source_target},
            "oracle": {"target_current_id": truth}}


def build_design():
    cases = []
    # Development controls exercise exact-ID/path continuation. These rows are
    # excluded from the held-out coverage and false-rebind statistics.
    for i in range(60):
        seed = 1000 + i
        source, ids = base_graph(seed, "source")
        current = json.loads(json.dumps(source))
        cases.append(case(f"dev-{i:03d}", "development", "identity_persistent", seed,
                          source, current, ids["target"], ids["target"]))

    positive_families = ("sibling_reorder", "insert_duplicate_save", "transparent_wrapper")
    i = 0
    for family_index, family in enumerate(positive_families):
        for j in range(100):
            seed = 2000 + family_index * 100 + j
            source, source_ids = base_graph(seed, "source")
            current, current_ids = relabel_current(seed, family)
            # Vary serialized node order independently from structure.
            random.Random(seed * 31 + 7).shuffle(current["nodes"])
            cases.append(case(f"heldout-pos-{i:03d}", "heldout_positive", family, seed,
                              source, current, source_ids["target"], current_ids["target"]))
            i += 1

    i = 0
    negative_counts = (("automorphism", 200), ("removed_target", 150), ("semantic_role_change", 150))
    for family, count in negative_counts:
        for j in range(count):
            seed = 5000 + i
            source, current, source_target, truth = mutate_negative(seed, family)
            random.Random(seed * 17 + 3).shuffle(current["nodes"])
            cases.append(case(f"heldout-neg-{i:03d}", "heldout_negative", family, seed,
                              source, current, source_target, truth))
            i += 1
    return {"schema": "issue-8675-cross-revision-graphs-v1", "cases": cases}


if __name__ == "__main__":
    json.dump(build_design(), sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
