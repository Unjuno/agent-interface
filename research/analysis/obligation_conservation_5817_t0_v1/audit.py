import copy
import json
import pathlib
import sys


END_STATES = {"RESOLVED_VERIFIED", "COMPENSATED_VERIFIED", "PARTIAL_KNOWN"}


def oracle(case, terminal):
    records = {}
    transitions = []
    prefixes = []
    for e in case["events"]:
        action, oid = e["op"], e["id"]
        if action in ("create", "create_child"):
            if oid in records:
                transitions.append({"op": action, "id": oid, "accepted": False, "reason": "DUPLICATE_ID"})
                continue
            records[oid] = {"id": oid, "owner": e.get("owner"), "fallback": e.get("fallback"),
                            "resource": e["resource"], "status": e["status"], "children": [],
                            "no_owner_stop": e.get("owner") is None}
            parent = e.get("parent")
            if parent is not None and parent in records:
                records[parent]["children"].append(oid)
            transitions.append({"op": action, "id": oid, "accepted": True})
        elif action == "timeout":
            records[oid]["escalated"] = True
            transitions.append({"op": action, "id": oid, "accepted": True, "discharged": False})
        elif action == "escalate":
            records[oid]["routing"] = "EXPLICITLY_ESCALATED"
            transitions.append({"op": action, "id": oid, "accepted": True, "discharged": False})
        elif action == "transfer":
            if e["accepted"]:
                records[oid]["owner"] = e["to"]
                records[oid]["no_owner_stop"] = False
            transitions.append({"op": action, "id": oid, "accepted": e["accepted"],
                                "owner": records[oid]["owner"], "discharged": False})
        elif action == "crash":
            fallback = records[oid]["fallback"]
            records[oid]["owner"] = fallback
            records[oid]["no_owner_stop"] = fallback is None
            transitions.append({"op": action, "id": oid, "owner": fallback,
                                "no_owner_stop": fallback is None, "discharged": False})
        elif action == "resolve":
            accepted = e.get("verified") is True and e.get("evidence") in {"effect_readback", "release_readback"}
            if accepted:
                records[oid]["status"] = "RESOLVED_VERIFIED"
            transitions.append({"op": action, "id": oid, "accepted": accepted,
                                "discharged": accepted, "status": records[oid]["status"]})
        elif action == "close_parent":
            can_close = all(records[c]["status"] in terminal for c in records[oid]["children"])
            records[oid]["parent_closed"] = can_close
            transitions.append({"op": action, "id": oid, "accepted": can_close, "discharged": False})
        elif action == "compensate":
            child = e["child"]
            accepted = child not in records
            if accepted:
                records[child] = {"id": child, "owner": e["owner"], "fallback": None,
                                  "resource": e["resource"], "status": "UNKNOWN_PENDING",
                                  "children": [], "no_owner_stop": False}
                records[oid]["children"].append(child)
            transitions.append({"op": action, "id": oid, "child": child,
                                "accepted": accepted, "original_discharged": False})
        prefixes.append({"obligations": copy.deepcopy(list(records.values())),
                         "outstanding": sum(o["status"] not in terminal for o in records.values())})
    aliases = case.get("aliases", {})

    def root(name):
        visited = set()
        while name in aliases and name not in visited:
            visited.add(name)
            name = aliases[name]
        return name

    decisions = []
    for task in case["next"]:
        active = [o for o in records.values() if o["status"] not in terminal]
        if task["footprint"] is None:
            intersect = None
        else:
            normalized = set(map(root, task["footprint"]))
            intersect = any(root(o["resource"]) in normalized for o in active)
        decisions.append({"task": task["id"], "overlap": intersect,
                          "policies": {"task_status_only": True,
                                       "global_wait": len(active) == 0,
                                       "ledger_dependency": False if intersect is None else not intersect}})
    obligations = [{"id": o["id"], "owner": o["owner"], "resource": o["resource"], "status": o["status"],
                    "children": o["children"], "no_owner_stop": o["no_owner_stop"],
                    "routing": o.get("routing"),
                    "parent_closed": o.get("parent_closed", False),
                    "representation": "TERMINAL" if o["status"] in terminal else
                    ("NO_OWNER_STOP" if o["no_owner_stop"] else "OWNED_UNRESOLVED")}
                   for o in records.values()]
    return {"events": transitions, "prefixes": prefixes, "obligations": obligations, "decisions": decisions,
            "outstanding": sum(o["status"] not in terminal for o in obligations)}


def verify(actual, fixture):
    expected = {case["id"]: oracle(case, set(fixture["terminal"])) for case in fixture["cases"]}
    if actual != expected:
        raise ValueError("candidate differs from independent event/obligation/admission reconstruction")
    for case_id, result in actual.items():
        for item in result["obligations"]:
            if item["status"] not in END_STATES and item["representation"] not in {"OWNED_UNRESOLVED", "NO_OWNER_STOP"}:
                raise ValueError(f"unrepresented live obligation in {case_id}/{item['id']}")
        if result["outstanding"] != sum(x["status"] not in END_STATES for x in result["obligations"]):
            raise ValueError(f"outstanding count mismatch in {case_id}")
        case = next(row for row in fixture["cases"] if row["id"] == case_id)
        expected_prefix_created = 0
        for index, (prefix, event) in enumerate(zip(result["prefixes"], case["events"])):
            expected_prefix_created += int(event["op"] in {"create", "create_child"})
            expected_prefix_created += int(event["op"] == "compensate" and
                                            event["child"] not in {o["id"] for o in
                                                (result["prefixes"][index - 1]["obligations"] if index else [])})
            if len(prefix["obligations"]) != expected_prefix_created:
                raise ValueError(f"obligation ID lost or invented at {case_id} prefix {index}")
            if prefix["outstanding"] != sum(o["status"] not in END_STATES for o in prefix["obligations"]):
                raise ValueError(f"conservation count changed at {case_id} prefix {index}")
            for obligation in prefix["obligations"]:
                if obligation["status"] not in END_STATES and obligation["owner"] is None and not obligation["no_owner_stop"]:
                    raise ValueError(f"unowned unresolved obligation without explicit stop at {case_id} prefix {index}")
    must_remain = ("timeout_dependency", "accepted_transfer", "unaccepted_transfer", "crash_with_fallback",
                   "crash_without_fallback", "parent_release_child", "compensation_emits_child", "duplicate_compensation")
    if any(actual[key]["outstanding"] == 0 for key in must_remain):
        raise ValueError("unresolved obligation was discharged by a nonterminal event")
    if actual["verified_resolution"]["outstanding"] != 0:
        raise ValueError("verified resolution did not discharge its obligation")
    if actual["crash_without_fallback"]["obligations"][0]["representation"] != "NO_OWNER_STOP":
        raise ValueError("ownerless crash lacks explicit no-owner stop")
    if actual["duplicate_compensation"]["events"][-1]["accepted"]:
        raise ValueError("duplicate compensation child ID was accepted")
    for key in ("timeout_dependency", "resource_alias"):
        if not all(not row["policies"]["ledger_dependency"] for row in actual[key]["decisions"] if row["overlap"] is True):
            raise ValueError(f"dependent/aliased task admitted in {key}")
    independent = next(row for row in actual["timeout_dependency"]["decisions"] if row["task"] == "independent_read")
    if not independent["policies"]["ledger_dependency"] or independent["policies"]["global_wait"]:
        raise ValueError("independent work is not distinguished from global wait")
    dependent = actual["timeout_dependency"]["decisions"][0]
    if not dependent["policies"]["task_status_only"] or dependent["policies"]["ledger_dependency"]:
        raise ValueError("status-only comparator did not admit dependent work or ledger admitted it")
    if actual["timeout_dependency"]["obligations"][0].get("routing") != "EXPLICITLY_ESCALATED":
        raise ValueError("escalation routing was not retained on the unresolved obligation")
    unknown = actual["unknown_footprint"]["decisions"][0]
    if unknown["overlap"] is not None or unknown["policies"]["ledger_dependency"]:
        raise ValueError("unknown footprint did not fail closed")
    return {"audit": "PASS_METHOD_SCOPED", "cases": len(expected),
            "obligations": sum(len(x["obligations"]) for x in actual.values()),
            "created_obligation_ids": sum(len(x["obligations"]) for x in actual.values()),
            "corruption_controls_expected": 5, "errors": []}


def main():
    fixture = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    actual = json.load(sys.stdin)
    print(json.dumps(verify(actual, fixture), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
