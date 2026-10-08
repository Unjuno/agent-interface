import copy
import json
import sys


TERMINAL = {"RESOLVED_VERIFIED", "COMPENSATED_VERIFIED", "PARTIAL_KNOWN"}


def run_case(case, terminal):
    ledger = {}
    parents = {}
    events_out = []
    prefixes = []
    for event in case["events"]:
        op = event["op"]
        if op in ("create", "create_child"):
            oid = event["id"]
            if oid in ledger:
                events_out.append({"op": op, "id": oid, "accepted": False, "reason": "DUPLICATE_ID"})
                continue
            parent = event.get("parent")
            ledger[oid] = {"id": oid, "owner": event.get("owner"), "fallback": event.get("fallback"),
                           "resource": event["resource"], "status": event["status"], "children": [],
                           "no_owner_stop": event.get("owner") is None}
            if parent is not None and parent in ledger:
                ledger[parent]["children"].append(oid)
                parents[oid] = parent
            events_out.append({"op": op, "id": oid, "accepted": True})
        elif op == "timeout":
            ledger[event["id"]]["escalated"] = True
            events_out.append({"op": op, "id": event["id"], "accepted": True, "discharged": False})
        elif op == "escalate":
            ledger[event["id"]]["routing"] = "EXPLICITLY_ESCALATED"
            events_out.append({"op": op, "id": event["id"], "accepted": True, "discharged": False})
        elif op == "transfer":
            item = ledger[event["id"]]
            if event["accepted"]:
                item["owner"] = event["to"]
                item["no_owner_stop"] = False
            events_out.append({"op": op, "id": event["id"], "accepted": event["accepted"],
                               "owner": item["owner"], "discharged": False})
        elif op == "crash":
            item = ledger[event["id"]]
            fallback = item["fallback"]
            item["owner"] = fallback
            item["no_owner_stop"] = fallback is None
            events_out.append({"op": op, "id": event["id"], "owner": fallback,
                               "no_owner_stop": fallback is None, "discharged": False})
        elif op == "resolve":
            item = ledger[event["id"]]
            valid = event.get("verified") is True and event.get("evidence") in ("effect_readback", "release_readback")
            if valid:
                item["status"] = "RESOLVED_VERIFIED"
            events_out.append({"op": op, "id": event["id"], "accepted": valid,
                               "discharged": valid, "status": item["status"]})
        elif op == "close_parent":
            item = ledger[event["id"]]
            ready = all(ledger[child]["status"] in terminal for child in item["children"])
            item["parent_closed"] = ready
            events_out.append({"op": op, "id": event["id"], "accepted": ready, "discharged": False})
        elif op == "compensate":
            child = event["child"]
            accepted = child not in ledger
            if accepted:
                ledger[child] = {"id": child, "owner": event["owner"], "fallback": None,
                                 "resource": event["resource"], "status": "UNKNOWN_PENDING",
                                 "children": [], "no_owner_stop": False}
                ledger[event["id"]]["children"].append(child)
                parents[child] = event["id"]
            events_out.append({"op": op, "id": event["id"], "child": child,
                               "accepted": accepted, "original_discharged": False})
        prefixes.append({"obligations": copy.deepcopy(list(ledger.values())),
                         "outstanding": sum(item["status"] not in terminal for item in ledger.values())})

    aliases = case.get("aliases", {})

    def canonical(resource):
        seen = set()
        while resource in aliases and resource not in seen:
            seen.add(resource)
            resource = aliases[resource]
        return resource

    decisions = []
    for task in case["next"]:
        unresolved = [o for o in ledger.values() if o["status"] not in terminal]
        if task["footprint"] is None:
            overlap = None
        else:
            footprint = {canonical(resource) for resource in task["footprint"]}
            overlap = any(canonical(o["resource"]) in footprint for o in unresolved)
        decisions.append({"task": task["id"], "overlap": overlap, "policies": {
            "task_status_only": True,
            "global_wait": not unresolved,
            "ledger_dependency": False if overlap is None else not overlap,
        }})
    rows = []
    for item in ledger.values():
        rows.append({"id": item["id"], "owner": item["owner"], "resource": item["resource"],
                     "status": item["status"], "children": item["children"],
                     "no_owner_stop": item["no_owner_stop"],
                     "routing": item.get("routing"),
                     "parent_closed": item.get("parent_closed", False),
                     "representation": "TERMINAL" if item["status"] in terminal else
                     ("NO_OWNER_STOP" if item["no_owner_stop"] else "OWNED_UNRESOLVED")})
    return {"events": events_out, "prefixes": prefixes, "obligations": rows, "decisions": decisions,
            "outstanding": sum(row["status"] not in terminal for row in rows)}


def main():
    fixture = json.load(sys.stdin)
    result = {case["id"]: run_case(case, set(fixture["terminal"])) for case in fixture["cases"]}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
