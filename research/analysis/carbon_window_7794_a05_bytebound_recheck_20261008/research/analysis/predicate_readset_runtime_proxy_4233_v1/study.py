import json
import sys
from collections.abc import Mapping
from pathlib import Path


def _path_text(path):
    return ".".join(path)


class TracedMapping(Mapping):
    """Read-only nested Mapping that records accessed mapping/key paths."""

    def __init__(self, value, path=(), reads=None):
        self._value = value
        self._path = path
        self._reads = reads if reads is not None else set()

    def __getitem__(self, key):
        child_path = self._path + (str(key),)
        self._reads.add(_path_text(child_path))
        value = self._value[key]
        if isinstance(value, Mapping):
            return TracedMapping(value, child_path, self._reads)
        return value

    def __iter__(self):
        self._reads.add(_path_text(self._path) or "<root-membership>")
        return iter(self._value)

    def __len__(self):
        self._reads.add(_path_text(self._path) or "<root-membership>")
        return len(self._value)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


def ready_to_submit(context):
    mode = context["form"]["mode"]
    if mode != "submit":
        return "DEFER"
    risk = context["risk"]["level"]
    return "ALLOW" if risk == "safe" else "YIELD"


def target_match(context):
    return context["target"]["id"] == context["intent"]["target_id"]


PREDICATES = {
    "READY_TO_SUBMIT": ready_to_submit,
    "TARGET_MATCH": target_match,
}
STATIC_DECLARED = {
    "READY_TO_SUBMIT": ("form.mode",),
    "TARGET_MATCH": ("target.id", "intent.target_id"),
}


def _generation(snapshot, path):
    return snapshot["generations"].get(path, 0)


def _fingerprint(snapshot, paths):
    return tuple((path, _generation(snapshot, path)) for path in sorted(paths))


def _full_paths(snapshot):
    return tuple(sorted(snapshot["generations"]))


def _call(predicate, snapshot, traced):
    reads = set()
    context = TracedMapping(snapshot["context"], reads=reads) if traced else snapshot["context"]
    value = predicate(context)
    return value, tuple(sorted(reads))


def _policy_step(policy, name, snapshot, cache):
    predicate = PREDICATES[name]
    previous = cache.get(name)
    if policy == "FULL_RECOMPUTE":
        value, reads = _call(predicate, snapshot, traced=False)
        return value, reads, "RECOMPUTE", "ORACLE", False

    if policy == "DYNAMIC_READSET":
        paths = previous["paths"] if previous else ()
    elif policy == "STATIC_DECLARED":
        paths = STATIC_DECLARED[name]
    elif policy == "STATIC_ALL":
        paths = _full_paths(snapshot)
    else:
        raise ValueError("unknown policy")

    current_fp = _fingerprint(snapshot, paths)
    if previous and previous["fingerprint"] == current_fp:
        return previous["value"], previous["paths"], "HIT", "UNCHANGED", True

    reason = "INITIAL" if not previous else "GENERATION_CHANGED"
    value, observed = _call(predicate, snapshot, traced=True)
    if policy == "DYNAMIC_READSET":
        paths = observed
    elif policy == "STATIC_DECLARED":
        paths = STATIC_DECLARED[name]
    else:
        paths = _full_paths(snapshot)
    cache[name] = {
        "value": value,
        "paths": tuple(paths),
        "fingerprint": _fingerprint(snapshot, paths),
    }
    return value, tuple(observed), "MISS", reason, False


def run(trace):
    rows = []
    state_by_id = {s["id"]: s for s in trace["states"]}
    for policy in trace["policies"]:
        cache = {}
        previous_values = {}
        for snapshot in trace["states"]:
            for name in trace["predicates"]:
                value, reads, action, cause, hit = _policy_step(
                    policy, name, snapshot, cache
                )
                oracle, _ = _call(PREDICATES[name], snapshot, traced=False)
                prev = previous_values.get(name)
                false_invalidation = action == "MISS" and prev is not None and prev == oracle
                rows.append({
                    "policy": policy,
                    "state": snapshot["id"],
                    "predicate": name,
                    "value": value,
                    "oracle_value": oracle,
                    "reads": list(reads),
                    "action": action,
                    "cause": cause,
                    "cache_hit": hit,
                    "unsafe_reuse": action == "HIT" and value != oracle,
                    "false_invalidation": false_invalidation,
                    "generations": snapshot["generations"],
                })
                previous_values[name] = oracle
    return rows


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -B study.py TRACE.json RAW.jsonl")
    trace = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rows = run(trace)
    Path(sys.argv[2]).write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({"rows": len(rows), "states": len(trace["states"]), "exit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
