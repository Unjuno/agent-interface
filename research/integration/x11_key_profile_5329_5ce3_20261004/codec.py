"""Deterministic selected-predicate codecs. No raw registry, action or oracle."""
import copy
def encode(policy,record):
    meta=copy.deepcopy(record["meta"]);o=record["observation"]
    b=bytes.fromhex(o["keymap"]);codes=meta["keycodes"]
    if len(b)!=32 or set(codes)!={"F8","F9"}or any(type(c)is not int or not 8<=c<=255 for c in codes.values())or codes["F8"]==codes["F9"]or type(o["scoped_verified"])is not bool:raise ValueError("invalid observation")
    k=sum(int(bool(b[c//8]&(1<<(c%8))))<<i for i,c in enumerate((codes["F8"],codes["F9"])))
    if policy=="RAW_CHECKPOINT":payload=copy.deepcopy(o)
    elif policy=="RECEIPT_TRUST":payload={"v":o["scoped_verified"]}
    elif policy in("KEY_SUBSET","CONSERVATIVE_PROFILE"):
        payload={"k":k,"b":o["buttons"],"v":o["scoped_verified"]}
        if policy=="CONSERVATIVE_PROFILE":
            residual=bytearray(b)
            for c in codes.values():residual[c//8]&=~(1<<(c%8))
            payload["o"]=any(residual)
    else:raise ValueError("unknown policy")
    return {"meta":meta,"payload":payload}
def decode(policy,packet):
    unknown={k:None for k in("owned_up","bystander_held","all_keys_neutral_buttons123","scoped_verified")}
    try:
        p=packet["payload"];m=packet["meta"];bystander=m["bystander_required"]
        if policy=="RAW_CHECKPOINT":
            b=bytes.fromhex(p["keymap"]);c=m["keycodes"]
            if len(b)!=32 or type(p["scoped_verified"])is not bool:return unknown
            return {"owned_up":not bool(b[c["F8"]//8]&(1<<(c["F8"]%8))),"bystander_held":bool(b[c["F9"]//8]&(1<<(c["F9"]%8)))if bystander else None,"all_keys_neutral_buttons123":not any(b)and p["buttons"]==0,"scoped_verified":p["scoped_verified"]}
        if policy=="RECEIPT_TRUST":
            if type(p["v"])is not bool:return unknown
            return {"owned_up":p["v"],"bystander_held":None,"all_keys_neutral_buttons123":p["v"],"scoped_verified":p["v"]}
        if policy not in("KEY_SUBSET","CONSERVATIVE_PROFILE")or type(p["k"])is not int or not 0<=p["k"]<=3 or type(p["v"])is not bool:return unknown
        global_neutral=None
        if policy=="CONSERVATIVE_PROFILE":
            if type(p["o"])is not bool:return unknown
            global_neutral=p["k"]==0 and not p["o"]and p["b"]==0
        return {"owned_up":not bool(p["k"]&1),"bystander_held":bool(p["k"]&2)if bystander else None,"all_keys_neutral_buttons123":global_neutral,"scoped_verified":p["v"]}
    except (KeyError,ValueError,IndexError,TypeError):return unknown
