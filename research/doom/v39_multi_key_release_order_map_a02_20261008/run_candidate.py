"""Prototype per-actuation identity capture over the frozen PR #7692 source."""
import ast
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "session_map01_v19.py"
SOURCE_SHA256 = "2c5304bd246118f8124d5f7b50b81f869fb35ea3ee76887f4682748fdf95618a"
IDENTITY = ("id", "step", "owner_id", "intent_token", "key", "actuation_id")


def exact_identity(row):
    if type(row) is not dict or any(field not in row for field in IDENTITY):
        return None
    if (type(row["id"]) is not str or type(row["step"]) is not int or
            type(row["owner_id"]) is not str or type(row["intent_token"]) is not str or
            type(row["key"]) is not str or type(row["actuation_id"]) is not str):
        return None
    return tuple(row[field] for field in IDENTITY)


class FakeBackend:
    def __init__(self, emit):
        self.emit = emit
        self.held = set()


def make_capture_backend(state):
    """Candidate drop-in wrapper shape; emits unchanged telemetry first."""
    class CapturingBackend(FakeBackend):
        def capture(self, row):
            self.emit(row)
            event = row.get("event")
            if event not in ("input_admission", "input_release_measurement"):
                return
            state["backend"] = self
            if event == "input_admission":
                key = exact_identity(row)
                state["candidate"] = None
                if key is None or key in state["admissions"]:
                    state["ambiguous"] = True
                    return
                state["admissions"][key] = dict(row)
                return
            key = exact_identity(row)
            down = state["admissions"].pop(key, None) if key is not None else None
            if down is None or self.held or state["ambiguous"]:
                state["candidate"] = None
                return
            state["candidate"] = (down, dict(row), list(self.held))

    return CapturingBackend


def permute(keys, release_order):
    state = {"admissions": {}, "candidate": None, "ambiguous": False}
    emitted = []
    backend = make_capture_backend(state)(emitted.append)
    identities = {
        key: {"id": "program-0", "step": index, "owner_id": "owner-0",
              "intent_token": "intent-0", "key": key,
              "actuation_id": "act-" + key}
        for index, key in enumerate(keys)
    }
    for key in keys:
        backend.held.add(key)
        backend.capture({"event": "input_admission", **identities[key]})
    for key in release_order:
        backend.held.remove(key)
        backend.capture({"event": "input_release_measurement", **identities[key]})
    candidate = state["candidate"]
    matched = (candidate is not None and not state["ambiguous"] and
               exact_identity(candidate[0]) == exact_identity(candidate[1]) and
               candidate[2] == [])
    return {"admission_order": list(keys), "release_order": list(release_order),
            "matched": matched,
            "candidate_down_key": None if candidate is None else candidate[0]["key"],
            "candidate_up_key": None if candidate is None else candidate[1]["key"],
            "held_after": None if candidate is None else candidate[2],
            "pending_admissions": len(state["admissions"]),
            "ambiguous": state["ambiguous"]}


def mutation_checks():
    checks = {}
    row = {"id": "p", "step": 0, "owner_id": "o", "intent_token": "i",
           "key": "A", "actuation_id": "a"}
    for field in IDENTITY:
        invalid = dict(row)
        invalid[field] = None
        checks[f"missing_{field}"] = exact_identity(invalid) is None
    invalid_bool_alias = dict(row, step=True)
    checks["bool_step_rejected"] = exact_identity(invalid_bool_alias) is None

    state = {"admissions": {}, "candidate": None, "ambiguous": False}
    emitted = []
    backend = make_capture_backend(state)(emitted.append)
    backend.held.add("A")
    backend.capture({"event": "input_admission", **row})
    backend.capture({"event": "input_admission", **row})
    checks["duplicate_admission_marks_ambiguous"] = state["ambiguous"]
    backend.held.remove("A")
    backend.capture({"event": "input_release_measurement", **row})
    checks["ambiguous_identity_has_no_candidate"] = state["candidate"] is None

    state = {"admissions": {}, "candidate": None, "ambiguous": False}
    emitted = []
    backend = make_capture_backend(state)(emitted.append)
    backend.held.add("A")
    backend.capture({"event": "input_admission", **row})
    backend.held.remove("A")
    wrong_release = dict(row, actuation_id="wrong-actuation")
    backend.capture({"event": "input_release_measurement", **wrong_release})
    checks["mismatched_release_has_no_candidate"] = state["candidate"] is None
    return checks


def main():
    source_bytes = SOURCE.read_bytes()
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f"source SHA-256 mismatch: {digest}")
    tree = ast.parse(source_bytes, filename=str(SOURCE))
    capture = next(node for node in tree.body
                   if isinstance(node, ast.FunctionDef) and
                   node.name == "_capture_backend")
    capture_text = ast.get_source_segment(source_bytes.decode("utf-8"), capture)
    if "state[\"admission\"] = dict(row)" not in capture_text:
        raise SystemExit("pinned baseline no longer has a single admission slot")
    cases = []
    for n in (1, 2, 3):
        keys = tuple(chr(ord("A") + i) for i in range(n))
        rows = [permute(admission, release)
                for admission in itertools.permutations(keys)
                for release in itertools.permutations(keys)]
        cases.append({"key_count": n, "schedule_count": len(rows),
                      "matched": sum(row["matched"] for row in rows),
                      "censored": sum(not row["matched"] for row in rows),
                      "match_rate": sum(row["matched"] for row in rows) / len(rows),
                      "schedules": rows})
    result = {
        "schema": "issue59-pr7692-release-order-map-a02-v1",
        "kind": "offline_source_pinned_candidate_construction",
        "source": {"pr": 7692, "head": "7ec4e3ef405919bf5f1bfd9eeddbe630f3a5b32e",
                   "path": "research/doom/session_map01_v19.py",
                   "sha256": digest},
        "identity_fields": list(IDENTITY),
        "hypothesis": "A per-actuation identity map can retain the DOWN corresponding to the final UP, independent of admission and release order, while still requiring exact identity and an empty final held set.",
        "cases": cases,
        "mutation_checks": mutation_checks(),
        "limits": "Synthetic unique per-key events only. No V39 compiler, scorer tail, physical input, live frequency, GUI, model, or task effect was run.",
        "decision": "PASS_CANDIDATE if all 41 schedules match exact final DOWN/UP identity with empty held state and every malformed, duplicate, or mismatched identity mutation is rejected."
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{key: value for key, value in case.items() if key != "schedules"}
                      for case in cases], indent=2))


if __name__ == "__main__":
    main()
