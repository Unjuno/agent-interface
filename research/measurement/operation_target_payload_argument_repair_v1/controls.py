from replay import normalized_disp

def conflict(items):
    common=None
    for candidates,accepted in items:
        p={"candidates":candidates}
        s={normalized_disp(p,d) for d in accepted}
        common=s if common is None else common&s
    return not bool(common)

a=([{"id":"a","role":"button","ops":["CLICK"]}],[{"op":"CLICK","target":"a"}])
b=([{"id":"b","role":"button","ops":["CLICK"]}],[{"op":"CLICK","target":"b"}])
assert conflict([a,b]) is False
assert conflict([a,([{"id":"c","role":"button","ops":["CLICK"]}],[{"op":"YIELD","reason":"STALE_STATE"}])]) is True
t1=([{"id":"f1","role":"field","ops":["TYPE_TEXT"]}],[{"op":"TYPE_TEXT","target":"f1","payload_ref":"p1"}])
t2=([{"id":"f2","role":"field","ops":["TYPE_TEXT"]}],[{"op":"TYPE_TEXT","target":"f2","payload_ref":"p2"}])
assert conflict([t1,t2]) is False
assert conflict([t1,([{"id":"f3","role":"field","ops":["TYPE_TEXT"]}],[{"op":"YIELD","reason":"PAYLOAD_MISSING"}])]) is True
print("normalizer_construction=4/4")
