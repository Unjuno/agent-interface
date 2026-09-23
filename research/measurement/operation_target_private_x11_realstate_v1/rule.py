FULL_OPS={"CLICK","TYPE_TEXT","SCROLL"}

def decide(p):
    adm=p["target_admissibility"]
    if adm=="STALE": return {"op":"YIELD","reason":"STALE_STATE"}
    if adm=="AMBIGUOUS": return {"op":"YIELD","reason":"AMBIGUOUS_TARGET"}
    if adm=="MISSING": return {"op":"YIELD","reason":"MISSING_TARGET"}
    if adm=="NOT_REQUIRED":
        if set(p["allowed_operations"])!=FULL_OPS:
            return {"op":"YIELD","reason":"UNSUPPORTED_OPERATION"}
        return {"op":"NO_LOCAL_ACTION","reason":"ALREADY_SATISFIED"}
    if adm!="CURRENT": return {"op":"YIELD","reason":"UNSUPPORTED_OR_MALFORMED"}
    fields=[c for c in p["candidates"] if c["role"]=="field" and "TYPE_TEXT" in c["ops"]]
    if fields:
        if p["payload_ref"] is None: return {"op":"YIELD","reason":"PAYLOAD_MISSING"}
        return {"op":"TYPE_TEXT","target":fields[0]["id"],"payload_ref":p["payload_ref"]}
    scrolls=[c for c in p["candidates"] if c["role"]=="scroll_region" and "SCROLL" in c["ops"]]
    if scrolls: return {"op":"SCROLL","target":scrolls[0]["id"]}
    buttons=[c for c in p["candidates"] if c["role"]=="button" and "CLICK" in c["ops"]]
    if buttons: return {"op":"CLICK","target":buttons[0]["id"]}
    return {"op":"YIELD","reason":"UNSUPPORTED_OR_MALFORMED"}
