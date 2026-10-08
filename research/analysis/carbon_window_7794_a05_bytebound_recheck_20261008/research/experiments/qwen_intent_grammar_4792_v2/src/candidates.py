"""State-only candidate construction and a token trie for paired decoding."""
import json


YIELD_REASONS = ("forbidden", "ambiguous", "stale_scope", "missing_evidence", "unsupported")
NO_ACTION_REASONS = ("already_satisfied", "not_requested")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def candidates_from_state(state):
    """Build candidates only from visible state; never accept or inspect a label."""
    values = set()
    allowed_effects = set(state.get("allowed_effects", []))
    for field, options in state.get("allowed_values", {}).items():
        if f"set_{field}" in allowed_effects:
            for value in options:
                if isinstance(field, str) and isinstance(value, str):
                    values.add(canonical({"op": "set", "field": field, "value": value}))
    if "save_settings" in allowed_effects:
        values.add(canonical({"op": "save"}))
    for target in set(state.get("visible_targets", [])) & allowed_effects:
        if isinstance(target, str) and target.startswith("toggle_"):
            values.add(canonical({"op": "toggle", "target": target}))
    for reason in YIELD_REASONS:
        values.add(canonical({"op": "yield", "reason": reason}))
    for reason in NO_ACTION_REASONS:
        values.add(canonical({"op": "no_action", "reason": reason}))
    return sorted(values)


class TokenTrie:
    def __init__(self, token_paths, eos_token_id):
        self.root = {}
        self.eos_token_id = int(eos_token_id)
        for path in token_paths:
            node = self.root
            for token_id in path:
                node = node.setdefault(int(token_id), {})
            node[None] = True

    def allowed(self, completion_prefix):
        node = self.root
        for token_id in completion_prefix:
            child = node.get(int(token_id))
            if not isinstance(child, dict):
                return []
            node = child
        choices = [token for token in node if token is not None]
        if node.get(None) is True:
            choices.append(self.eos_token_id)
        return sorted(set(choices))

    def prefix_receipt(self, token_paths):
        """Exhaustively enumerate the frozen path prefixes and their next IDs."""
        receipts = []
        prefixes = {()}
        for path in token_paths:
            prefixes.update(tuple(path[:i]) for i in range(1, len(path) + 1))
        for prefix in sorted(prefixes):
            receipts.append({"prefix": list(prefix), "allowed": self.allowed(prefix)})
        return receipts
