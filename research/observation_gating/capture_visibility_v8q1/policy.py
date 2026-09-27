"""Pure parent-only rectangle assessment. Not a generic screenshot policy."""

def assess(evidence):
    out = dict(status="UNKNOWN", input_authority=False, task_success=None)
    if type(evidence) is not dict or set(evidence) != {
        "map_state", "visibility", "region", "children", "coverage_complete"
    }:
        return out
    if evidence["coverage_complete"] is not True:
        return out
    if type(evidence["map_state"]) is not int or evidence["map_state"] != 2:
        return out
    if type(evidence["visibility"]) is not int or evidence["visibility"] != 0:
        return out
    r = evidence["region"]
    if type(r) is not list or len(r) != 4 or any(type(v) is not int for v in r):
        return out
    x,y,w,h = r
    if w <= 0 or h <= 0 or type(evidence["children"]) is not list:
        return out
    for child in evidence["children"]:
        if type(child) is not dict or set(child) != {"map_state", "class", "rect"}:
            return out
        if any(type(child[k]) is not int for k in ("map_state", "class")):
            return out
        if child["map_state"] not in (0,1,2) or child["class"] not in (1,2):
            return out
        q = child["rect"]
        if type(q) is not list or len(q) != 4 or any(type(v) is not int for v in q):
            return out
        a,b,c,d = q
        if c <= 0 or d <= 0:
            return out
        if child["map_state"] == 2 and child["class"] == 1:
            if a < x+w and x < a+c and b < y+h and y < b+d:
                return out
    out["status"] = "CLEAR_PARENT_REGION_SCOPED"
    return out
