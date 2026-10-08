from __future__ import annotations
import hashlib,json,random
from oracle import acceptable_from_facts
from schema import canon_disp

ROLE_ORDER=(
    "CLICK_UNIQUE","CLICK_MULTI","TYPE_PAYLOAD","SCROLL_MULTI",
    "NO_ACTION","MISSING_TARGET","AMBIGUOUS_TARGET","ROTATING_NEGATIVE",
)
ROTATING=("STALE_STATE","UNSUPPORTED_OPERATION","PAYLOAD_MISSING")

def _target(tid, *, present=True, compatible=True, acceptable=True, role="button"):
    return {"id":tid,"role":role,"present":present,"compatible":compatible,"acceptable":acceptable}

def _base(unit,role,rng):
    obs=f"obs-{unit:02d}-{rng.randrange(10**9):09d}"
    bind=f"bind-{unit:02d}"
    packet={
        "intent_id":f"intent-{unit%4}","observation_id":obs,"state_epoch":1000+unit,
        "binding_id":bind,"allowed_operations":["CLICK","TYPE_TEXT","SCROLL"],
        "payload_ref_present":False,"candidates":[]
    }
    facts={
        "operation":"CLICK","targets":[],"requires_target":True,"ambiguous":False,
        "required_payload":False,"payload_available":False,"payload_ref":None,
        "semantic_no_action":False,"hard_invalid":False,"unsupported_operation":False,
    }
    excluded={"future_effect":f"effect-{unit}-{role}","post_state":f"post-{unit}-{role}","evaluator_state":"HIDDEN"}
    return packet,facts,excluded

def make_row(unit, role, rng):
    packet,facts,excluded=_base(unit,role,rng)
    if role=="CLICK_UNIQUE":
        facts["operation"]="CLICK"; facts["targets"]=[_target(f"u{unit}-save")]
        packet["candidates"]=[{"id":f"u{unit}-save","role":"button","ops":["CLICK"]}]
    elif role=="CLICK_MULTI":
        facts["operation"]="CLICK"; facts["targets"]=[_target(f"u{unit}-a"),_target(f"u{unit}-b")]
        packet["candidates"]=[{"id":f"u{unit}-a","role":"button","ops":["CLICK"]},{"id":f"u{unit}-b","role":"button","ops":["CLICK"]}]
    elif role=="TYPE_PAYLOAD":
        facts["operation"]="TYPE_TEXT"; facts["required_payload"]=True; facts["payload_available"]=True; facts["payload_ref"]=f"payload-{unit}"; facts["targets"]=[_target(f"u{unit}-field",role="field")]
        packet["payload_ref_present"]=True; packet["candidates"]=[{"id":f"u{unit}-field","role":"field","ops":["TYPE_TEXT"]}]
    elif role=="SCROLL_MULTI":
        facts["operation"]="SCROLL"; facts["targets"]=[_target(f"u{unit}-pane1",role="scroll_region"),_target(f"u{unit}-pane2",role="scroll_region")]
        packet["candidates"]=[{"id":f"u{unit}-pane1","role":"scroll_region","ops":["SCROLL"]},{"id":f"u{unit}-pane2","role":"scroll_region","ops":["SCROLL"]}]
    elif role=="NO_ACTION":
        facts["semantic_no_action"]=True; facts["requires_target"]=False; facts["targets"]=[]
        packet["candidates"]=[]
    elif role=="MISSING_TARGET":
        facts["operation"]="CLICK"; facts["targets"]=[]
        packet["candidates"]=[]
    elif role=="AMBIGUOUS_TARGET":
        facts["operation"]="CLICK"; facts["ambiguous"]=True; facts["targets"]=[_target(f"u{unit}-x"),_target(f"u{unit}-y")]
        packet["candidates"]=[{"id":f"u{unit}-x","role":"button","ops":["CLICK"]},{"id":f"u{unit}-y","role":"button","ops":["CLICK"]}]
    elif role=="ROTATING_NEGATIVE":
        kind=ROTATING[unit%len(ROTATING)]
        if kind=="STALE_STATE":
            facts["hard_invalid"]=True; facts["targets"]=[_target(f"u{unit}-stale")]
            packet["candidates"]=[{"id":f"u{unit}-stale","role":"button","ops":["CLICK"]}]
        elif kind=="UNSUPPORTED_OPERATION":
            facts["unsupported_operation"]=True; facts["requires_target"]=False
            packet["allowed_operations"]=["CLICK","TYPE_TEXT"]
        else:
            facts["operation"]="TYPE_TEXT"; facts["required_payload"]=True; facts["payload_available"]=False; facts["targets"]=[_target(f"u{unit}-field2",role="field")]
            packet["candidates"]=[{"id":f"u{unit}-field2","role":"field","ops":["TYPE_TEXT"]}]
    else: raise ValueError(role)
    acceptable=acceptable_from_facts(facts)
    negative=all(d["op"] in ("NO_LOCAL_ACTION","YIELD") for d in acceptable)
    alt=len([d for d in acceptable if d["op"] in ("CLICK","TYPE_TEXT","SCROLL")])>=2
    row={
        "row_id":f"u{unit:02d}-{role.lower()}","scenario_unit_id":f"scenario-{unit:02d}",
        "split_group_id":f"scenario-{unit:02d}","split":"train" if unit<8 else "eval",
        "role":role,"candidate_input":packet,"oracle_facts":facts,"excluded_fields":excluded,
        "acceptable":acceptable,"semantic_negative":negative,"target_alternatives":alt,
        "grants_input_authority":False,
    }
    return row

def generate(seed, units=12):
    rng=random.Random(seed); rows=[]
    for u in range(units):
        for role in ROLE_ORDER: rows.append(make_row(u,role,rng))
    return rows

def corpus_digest(rows):
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":")).encode()).hexdigest()
