"""Build the public graph corpus and isolated hidden exact worlds."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/FORMAL_A01"

def edge(eid, src, dst, epoch, options, unit="px", context="ctx-A"):
    return {"id": eid, "src": src, "dst": dst, "epoch": epoch, "unit": unit,
            "context": context, "options": options}

def case(cid, kind, edges, target_frame, target, action_frame, action, intended, forbidden,
         baseline=None, valid=True, reason=""):
    return {"case_id": cid, "kind": kind, "epoch": 2, "unit": "px", "context": "ctx-A",
            "edges": edges, "target": {"frame": target_frame, "box": target, "identity": "target-1"},
            "action": {"frame": action_frame, "point": action, "target_identity": "target-1"},
            "intended": intended, "forbidden": forbidden, "baseline": baseline,
            "valid": valid, "invalid_reason": reason}

def main():
    ident = [{"sx": 1, "sy": 1, "tx": 0, "ty": 0}]
    shift = [{"sx": 1, "sy": 1, "tx": x, "ty": 0} for x in (-1, 1)]
    scale = [{"sx": 2, "sy": 2, "tx": 0, "ty": 0}]
    # Points are chosen so all worlds in valid-composed cases safely hit target.
    shared = edge("e-shared", "capture", "input", 2, shift)
    crop = edge("e-crop", "capture", "client", 2, ident)
    dpi = edge("e-dpi", "client", "monitor", 2, scale)
    monitor = edge("e-monitor", "monitor", "input", 2, ident)
    old = edge("e-old", "capture@1", "client@2", 2, ident)
    update = edge("e-update", "client@2", "input", 2, ident)
    cases = [
        case("DIRECT_STABLE", "direct", [shared], "capture", [9, 9, 11, 11], "capture", [10, 10], [9, 9, 11, 11], [[30,30,31,31]], {"sx":1,"sy":1,"tx":0,"ty":0}),
        case("DIRECT_TRANSLATION_UPDATED", "direct", [shared], "capture", [9, 9, 11, 11], "capture", [10, 10], [9, 9, 11, 11], [[30,30,31,31]], {"sx":1,"sy":1,"tx":1,"ty":0}),
        case("DIRECT_UNIFORM_SCALE_UPDATED", "direct", [edge("e-scale", "capture", "input", 2, scale)], "capture", [4,4,6,6], "capture", [5,5], [8,8,12,12], [[40,40,42,42]], {"sx":2,"sy":2,"tx":0,"ty":0}),
        case("COMPOSE_MIXED_DPI", "composed", [crop, dpi, monitor], "capture", [4,4,6,6], "capture", [5,5], [8,8,12,12], [[40,40,42,42]], None),
        case("COMPOSE_EPOCH_UPDATE", "composed", [old, update], "capture@1", [9,9,11,11], "capture@1", [10,10], [9,9,11,11], [[30,30,31,31]], None),
        case("COMPOSE_GENERAL_CHAIN", "composed", [edge("g1","capture","crop",2,ident), edge("g2","crop","client",2,ident), edge("g3","client","input",2,ident)], "capture", [9,9,11,11], "capture", [10,10], [9,9,11,11], [[30,30,31,31]], None),
        case("SHARED_UNCERTAINTY_CONTROL", "shared_control", [shared], "capture", [9,9,11,11], "capture", [10,10], [9,9,11,11], [[30,30,31,31]], {"sx":1,"sy":1,"tx":0,"ty":0}),
        case("INDEPENDENT_ERROR_CONTROL", "independent_control", [edge("ind-t","target-frame","input",2,shift), edge("ind-a","action-frame","input",2,shift)], "target-frame", [20,20,22,22], "action-frame", [21,20], [20,20,22,22], [[50,50,51,51]], None),
    ]
    invalids = [
        ("INVALID_STALE_EDGE", [edge("stale","capture","input",1,ident)], "capture", "capture", "stale_epoch"),
        ("INVALID_MISSING_EDGE", [], "capture", "capture", "missing_path"),
        ("INVALID_REVERSED_EDGE", [edge("rev","input","capture",2,ident)], "capture", "capture", "missing_path"),
        ("INVALID_DUPLICATE_PATH", [edge("dup1","capture","input",2,ident),edge("dup2","capture","input",2,ident)], "capture", "capture", "ambiguous_path"),
        ("INVALID_UNIT", [edge("unit","capture","input",2,ident,"dp")], "capture", "capture", "unit_mismatch"),
        ("INVALID_CONTEXT", [edge("ctx","capture","input",2,ident,"px","ctx-B")], "capture", "capture", "context_mismatch"),
    ]
    for cid, es, tf, af, why in invalids:
        c = case(cid,"invalid",es,tf,[9,9,11,11],af,[10,10],[9,9,11,11],[[30,30,31,31]],None,False,why)
        cases.append(c)
    c = case("INVALID_IDENTITY_SWAP","invalid",[shared],"capture",[9,9,11,11],"capture",[10,10],[9,9,11,11],[[30,30,31,31]],None,False,"identity_mismatch")
    c["action"]["target_identity"] = "neighbor-1"; cases.append(c)
    c = case("INVALID_NON_AFFINE_REFLOW","invalid",[shared],"capture",[9,9,11,11],"capture",[10,10],[9,9,11,11],[[30,30,31,31]],None,False,"unmodeled_reflow"); c["non_affine"] = True; cases.append(c)
    c = case("INVALID_FORBIDDEN_OVERLAP","composed",[edge("forbid","capture","input",2,ident)],"capture",[9,9,11,11],"capture",[10,10],[9,9,11,11],[[10,10,10,10]],None,True)
    cases.append(c)
    c = case("INVALID_TARGET_BOUNDARY","composed",[edge("boundary-target","target-frame","input",2,shift),edge("boundary-action","action-frame","input",2,shift)],"target-frame",[10,10,10,11],"action-frame",[10,10],[10,10,10,11],[[30,30,31,31]],None,True)
    cases.append(c)
    c = case("INVALID_STALE_BINDING","composed",[shared],"capture",[9,9,11,11],"capture",[10,10],[9,9,11,11],[[30,30,31,31]],None,False,"stale_binding"); c["binding_epoch"] = 1; cases.append(c)

    # Public graph hides edge-option truth by giving candidate the bounded sets only.
    public = [{k:v for k,v in x.items() if k not in ("intended", "valid", "invalid_reason")} for x in cases]
    (OUT/"public/cases.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in public))
    oracle = {x["case_id"]: {"valid": x["valid"], "reason": x["invalid_reason"], "target": x["intended"], "forbidden": x["forbidden"], "edge_options": {e["id"]: e["options"] for e in x["edges"]}} for x in cases}
    (OUT/"oracle/worlds.json").write_text(json.dumps(oracle,sort_keys=True,indent=2)+"\n")

if __name__ == "__main__": main()
