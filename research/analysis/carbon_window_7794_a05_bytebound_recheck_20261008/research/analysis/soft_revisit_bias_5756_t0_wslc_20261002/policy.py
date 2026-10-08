import re


def _terms(task):
    return {word for word in re.findall(r"[a-z0-9]+", task.lower()) if len(word) > 2}


def _cue(edge, terms):
    visible_words = set(re.findall(r"[a-z0-9]+", (edge["label"] + " " + edge.get("nearby", "")).lower()))
    return sum(term in visible_words for term in terms) + edge.get("saliency", 0) / 100


def choose_edge(observation, task, memory, policy):
    if policy not in {"stateless", "hard", "soft", "exhaustive"}:
        raise ValueError(f"unknown policy: {policy}")

    epoch = observation["source_epoch"]
    terms = _terms(task)
    safe = [edge for edge in observation["edges"] if edge["reversible"]]
    eligible = []
    for edge in safe:
        prior = memory.get(edge["id"], {})
        seen_in_epoch = prior.get("visits", 0) > 0 and prior.get("last_epoch") == epoch
        if policy in {"hard", "exhaustive"} and seen_in_epoch:
            continue
        if policy == "soft" and seen_in_epoch:
            revisitable = (not prior.get("inspection_complete", False)
                           or edge.get("revision_hint", False))
            if not revisitable or prior.get("visits", 0) >= 2:
                continue
        score = _cue(edge, terms)
        if policy == "soft" and seen_in_epoch:
            score += 2.0 if edge.get("revision_hint", False) else 0.0
            score += 2.0 if not prior.get("inspection_complete", False) else -1.0
        eligible.append((edge, score))

    if not eligible:
        return None
    if policy == "exhaustive":
        edge, _ = min(eligible, key=lambda pair: (pair[0].get("display_order", 0), pair[0]["id"]))
    else:
        edge, _ = max(eligible, key=lambda pair: (pair[1], pair[0]["id"]))
    return edge["id"]
