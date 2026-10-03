"""Raw-only independent reconstruction; imports no kernel/probe/test helpers."""
import copy
import hashlib
import json
from pathlib import Path
import sys

BOUNDARIES = {
    "observation": ("Observation", "record_observation", "new", "observed", "observation"),
    "binding": ("TargetBinding", "bind", "observed", "bound", "binding"),
    "authority": ("AuthorityLease", "authorize", "bound", "authorized", "lease"),
    "request": ("ExecutionRequest", "begin_execution", "authorized", "authorized", "request"),
    "execution": ("ExecutionReceipt", "record_execution", "authorized", "executed", "execution"),
    "effect": ("EffectReceipt", "record_effect", "executed", "verified", "effect"),
    "stop": ("ReleaseReceipt", "stop", "authorized", "stopped", "stop_reason"),
}
STATE_KEYS = {"stage", "observation", "binding", "lease", "request", "execution", "effect", "stop_reason"}


def fixtures():
    """Independent literal input contract, not copied from runtime factories."""
    def record(cls, **values): return {"type": cls, "fields": values}
    def enum(cls, value): return {"type": cls, "value": value}
    def seq(cls, values): return {"type": cls, "items": values}
    def digest(value): return hashlib.sha256(value.encode("ascii")).hexdigest()
    observation = record("Observation", sequence=7, captured_ns=100, surface_id="surface-a",
                         payload_sha256=digest("x"), width=1280, height=800, encoding="rgb24")
    binding = record("TargetBinding", target_id="save-button", observation_sequence=7,
                     surface_id="surface-a", binding_digest=digest("binding"))
    lease = record("AuthorityLease", lease_id="lease-1", observation_sequence=7, surface_id="surface-a",
                   valid_until_ns=1000, allowed_actions=seq("frozenset", [enum("ActionKind", "pointer"), enum("ActionKind", "text")]))
    action = record("Action", action_id="a1", kind=enum("ActionKind", "pointer"), operation="click")
    request = record("ExecutionRequest", command_id="cmd-1", invariant_manifest_id=digest("manifest"),
                     binding=binding, lease=lease, actions=seq("tuple", [action]))
    release = record("ReleaseReceipt", observed_ns=800, verified=True,
                     keys_down=seq("tuple", []), buttons_down=seq("tuple", []))
    execution = record("ExecutionReceipt", command_id="cmd-1", backend_receipt_id="backend-1",
                       invariant_manifest_id=digest("manifest"), lease_id="lease-1", observation_sequence=7,
                       surface_id="surface-a", started_ns=500, ended_ns=700, action_count=1,
                       effect_occurrence=enum("EffectOccurrence", "possible"), release=release)
    effect = record("EffectReceipt", command_id="cmd-1", invariant_manifest_id=digest("manifest"),
                    observed_ns=900, status=enum("EffectStatus", "verified"), evidence_digest=digest("effect"))
    return {"observation": observation, "binding": binding, "authority": lease, "request": request,
            "execution": execution, "effect": effect, "stop": release}


def same(a, b):
    if type(a) is not type(b): return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def audit(raw):
    errors = []
    if raw.get("schema") != "lifecycle-type-boundary-v1" or raw.get("revision") not in {"baseline", "candidate"}:
        return ["schema/revision"]
    rows = raw.get("rows")
    if type(rows) is not list or len(rows) != 28: return ["denominator"]
    expected_keys = {(b, f) for b in BOUNDARIES for f in ("typed", "shape", "none", "unrelated")}
    keys = [(r.get("boundary"), r.get("form")) for r in rows]
    if len(set(keys)) != 28 or set(keys) != expected_keys: errors.append("case identities")
    typed = {r["boundary"]: r for r in rows if r.get("form") == "typed"}
    independent = fixtures()
    for i, row in enumerate(rows):
        try:
            name, form = row["boundary"], row["form"]
            cls, method, start, end, field = BOUNDARIES[name]
            before, after, supplied = row["before"], row["after"], row["supplied"]
            if set(before) != STATE_KEYS or set(after) != STATE_KEYS: raise ValueError("state fields")
            if not same(before["stage"], {"type": "Stage", "value": start}): raise ValueError("start stage")
            if not same(before, typed[name]["before"]): raise ValueError("prerequisites differ by form")
            prefix = {"new": 0, "observed": 1, "bound": 2, "authorized": 3, "executed": 5}[start]
            if name in {"execution", "stop"}: prefix = 4
            expected_before = {key: None for key in STATE_KEYS}
            expected_before["stage"] = {"type": "Stage", "value": start}
            for depth, slot, fixture_name in ((1, "observation", "observation"), (2, "binding", "binding"),
                                               (3, "lease", "authority"), (4, "request", "request"),
                                               (5, "execution", "execution")):
                if depth <= prefix: expected_before[slot] = independent[fixture_name]
            if not same(before, expected_before): raise ValueError("independent prerequisite bytes")
            for slot, class_name, depth in (("observation", "Observation", 1), ("binding", "TargetBinding", 2),
                                           ("lease", "AuthorityLease", 3), ("request", "ExecutionRequest", 4),
                                           ("execution", "ExecutionReceipt", 5), ("effect", "EffectReceipt", 6)):
                if depth <= prefix:
                    if before[slot]["type"] != class_name: raise ValueError("prerequisite type")
                elif before[slot] is not None: raise ValueError("unexpected prior field")
            if before["stop_reason"] is not None: raise ValueError("prior stop")
            args = {"now_ns": 200} if name == "authority" else {"now_ns": 300} if name == "request" else {"reason": "cancelled"} if name == "stop" else {}
            if row["method"] != method or not same(row["arguments"], args): raise ValueError("call identity")
            if form == "typed":
                if supplied["type"] != cls: raise ValueError("typed supplied class")
                if not same(supplied, independent[name]): raise ValueError("typed fixture bytes")
            elif form == "none":
                if supplied is not None: raise ValueError("none supplied")
            elif form == "unrelated":
                if not same(supplied, {"type": "object"}): raise ValueError("unrelated supplied")
            else:
                reference = copy.deepcopy(typed[name]["supplied"])
                reference["type"] = "SimpleNamespace"
                if name == "binding": reference["fields"]["binding_digest"] = "bad"
                if name == "authority": reference["fields"]["allowed_actions"] = {"type": "frozenset", "items": []}
                if name == "request": reference["fields"]["actions"] = {"type": "tuple", "items": []}
                if name == "execution": reference["fields"]["ended_ns"] = 0
                if name == "effect": reference["fields"]["evidence_digest"] = "bad"
                if name == "stop": reference = {"type": "SimpleNamespace", "fields": {"released": True}}
                if not same(supplied, reference): raise ValueError("shaped supplied bytes")
            accept = form == "typed" or (raw["revision"] == "baseline" and form == "shape" and name != "observation")
            expect_after = copy.deepcopy(before)
            expected_outcome = None
            if accept:
                if row["exception"] is not None: raise ValueError("unexpected refusal")
                expect_after["stage"] = {"type": "Stage", "value": end}
                expect_after[field] = "cancelled" if name == "stop" else supplied
                if name in {"effect", "stop"}:
                    expected_outcome = {"type": "KernelOutcome", "fields": {
                        "stage": {"type": "Stage", "value": end}, "reason": "cancelled" if name == "stop" else end,
                        "command_id": "cmd-1", "effect_occurred": name == "effect",
                        "effect_verified": name == "effect", "release_verified": True}}
            else:
                exception = row["exception"]
                expected_exception = "ContractError"
                if raw["revision"] == "baseline" and name != "observation" and not (name == "stop" and form == "none"):
                    expected_exception = "AttributeError"
                if type(exception) is not dict or set(exception) != {"type", "message"} or exception["type"] != expected_exception or type(exception["message"]) is not str or not exception["message"]:
                    raise ValueError("typed refusal")
            if not same(after, expect_after): raise ValueError("state/mutation")
            if not same(row["outcome"], expected_outcome): raise ValueError("terminal outcome")
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f"row {i}: {exc}")
    return errors


def controls(raw):
    mutations = []
    def alter(name, fn):
        value = copy.deepcopy(raw)
        fn(value)
        if same(value, raw): raise RuntimeError("ineffective control " + name)
        mutations.append({"name": name, "rejected": bool(audit(value))})
    alter("missing row", lambda x: x["rows"].pop())
    alter("duplicate row", lambda x: x["rows"].__setitem__(1, copy.deepcopy(x["rows"][0])))
    alter("swallowed type refusal", lambda x: x["rows"][5].__setitem__("exception", None))
    alter("mutated refusal state", lambda x: x["rows"][5]["after"].__setitem__("binding", x["rows"][5]["supplied"]))
    alter("invalid-shaped input rewritten", lambda x: x["rows"][5]["supplied"]["fields"].__setitem__("binding_digest", "other"))
    alter("integer/bool terminal claim", lambda x: x["rows"][20]["outcome"]["fields"].__setitem__("effect_verified", 1))
    alter("fabricated terminal claim", lambda x: x["rows"][27].__setitem__("outcome", copy.deepcopy(x["rows"][24]["outcome"])))
    alter("call argument mismatch", lambda x: x["rows"][12]["arguments"].__setitem__("now_ns", 301))
    alter("typed fixture changed", lambda x: x["rows"][0]["supplied"]["fields"].__setitem__("sequence", 8))
    alter("prerequisite fixture changed", lambda x: x["rows"][16]["before"]["request"]["fields"].__setitem__("command_id", "other"))
    return mutations


if __name__ == "__main__":
    source = Path(sys.argv[1])
    raw = json.loads(source.read_text(encoding="utf-8"))
    errors = audit(raw)
    mutations = controls(raw) if raw.get("revision") == "candidate" and not errors else []
    result = {"raw_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "revision": raw.get("revision"),
              "rows": len(raw.get("rows", [])), "errors": errors, "controls": mutations,
              "status": "PASS_RAW_RECONSTRUCTION" if not errors and all(m["rejected"] for m in mutations) else "FAIL"}
    with Path(sys.argv[2]).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result))
    sys.exit(0 if result["status"] == "PASS_RAW_RECONSTRUCTION" else 1)
