from copy import deepcopy
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BD=HERE.parents[1]/'benchmark_discovery'
if BD.exists(): sys.path.insert(0,str(BD))
from mindustry_single_tile_score_v1 import score


def tile_map(state):
    return {(r["x"], r["y"]): r for r in state["tiles"]}


def canonical_state(plan, tick=100, copper=100):
    g=plan["guard"]
    tiles=[]
    for y in range(g["y_min"], g["y_max"]+1):
        for x in range(g["x_min"], g["x_max"]+1):
            row={"x":x,"y":y,"block":"air","team":0,"rotation":0}
            if [x,y] == plan["source"]:
                row={"x":x,"y":y,"block":"item-source","team":1,"rotation":0}
            tiles.append(row)
    return {"tiles":tiles,"source_item":"copper","core_x":145,"core_y":52,
            "copper":copper,"paused":True,"player_dead":False,"unit":{"plans":0},"tick":tick}


def positive_after(before, plan, wrong_rotation=False):
    out=deepcopy(before); m=tile_map(out); t=tuple(plan["target"])
    m[t]["block"]="conveyor"; m[t]["team"]=1; m[t]["rotation"]=0 if wrong_rotation else 1
    out["copper"] = before["copper"] - plan["expected_copper_cost"]
    out["tick"] = before["tick"] + 1
    return out


def verify_reset(canonical, reset_after, prev_epoch, epoch, plan):
    if epoch <= prev_epoch:
        return {"ok":False,"reason":"non_monotonic_epoch"}
    cm, rm = tile_map(canonical), tile_map(reset_after)
    if set(cm)!=set(rm): return {"ok":False,"reason":"guard_projection_mismatch"}
    target=tuple(plan["target"])
    if rm[target]["block"]!="air": return {"ok":False,"reason":"target_not_empty"}
    if rm != cm: return {"ok":False,"reason":"guard_not_canonical"}
    for k in ("source_item","core_x","core_y","copper","paused","player_dead"):
        if reset_after.get(k) != canonical.get(k): return {"ok":False,"reason":"state_not_canonical:"+k}
    if reset_after.get("unit") != canonical.get("unit"): return {"ok":False,"reason":"unit_not_canonical"}
    if reset_after["tick"] <= canonical["tick"]: return {"ok":False,"reason":"reset_tick_not_advanced"}
    return {"ok":True,"reason":None}


def controller_record(task, plan):
    return {"task_id":task["task_id"],"task":plan["task"],"layout":task["layout"],"benchmark_epoch":task["epoch"]}


def no_oracle_leak(record, fixture):
    return set(record)==set(fixture["controller_visible_keys"]) and not (set(record) & set(fixture["forbidden_controller_keys"]))


def run_valid(plan, fixture):
    rows=[]; prev_epoch=0; current=canonical_state(plan,100,100)
    for i,task in enumerate(fixture["task_order"]):
        before=deepcopy(current)
        after=positive_after(before,plan)
        evaluation=score(before,after,plan)
        visible=controller_record(task,plan)
        canonical_next=canonical_state(plan, after["tick"], 100)
        reset_after=deepcopy(canonical_next); reset_after["tick"] += 1
        reset=verify_reset(canonical_next,reset_after,prev_epoch,task["epoch"],plan)
        rows.append({"task_id":task["task_id"],"layout":task["layout"],"epoch":task["epoch"],
                     "task_evaluation":evaluation,"reset":reset,"controller_visible":visible,
                     "oracle_leak_free":no_oracle_leak(visible,fixture)})
        if evaluation["contract_satisfied"] is not True or reset["ok"] is not True:
            break
        prev_epoch=task["epoch"]
        current=reset_after
    return rows
