from replay import rule

def c(p,exp):
    got=rule(p);assert got==exp,(got,exp)
base={"allowed_operations":["CLICK","TYPE_TEXT","SCROLL"],"payload_ref_present":False,"payload_ref":None,"candidates":[]}
c({**base,"target_admissibility":"STALE"},{"op":"YIELD","reason":"STALE_STATE"})
c({**base,"target_admissibility":"MISSING"},{"op":"YIELD","reason":"MISSING_TARGET"})
c({**base,"target_admissibility":"AMBIGUOUS"},{"op":"YIELD","reason":"AMBIGUOUS_TARGET"})
c({**base,"target_admissibility":"NOT_REQUIRED"},{"op":"NO_LOCAL_ACTION","reason":"ALREADY_SATISFIED"})
c({**base,"target_admissibility":"NOT_REQUIRED","allowed_operations":["CLICK","TYPE_TEXT"]},{"op":"YIELD","reason":"UNSUPPORTED_OPERATION"})
c({**base,"target_admissibility":"CURRENT","candidates":[{"id":"f","role":"field","ops":["TYPE_TEXT"]}]},{"op":"YIELD","reason":"PAYLOAD_MISSING"})
c({**base,"target_admissibility":"CURRENT","payload_ref_present":True,"payload_ref":"p","candidates":[{"id":"f","role":"field","ops":["TYPE_TEXT"]}]},{"op":"TYPE_TEXT","target":"f","payload_ref":"p"})
c({**base,"target_admissibility":"CURRENT","candidates":[{"id":"b","role":"button","ops":["CLICK"]}]},{"op":"CLICK","target":"b"})
c({**base,"target_admissibility":"CURRENT","candidates":[{"id":"s","role":"scroll_region","ops":["SCROLL"]}]},{"op":"SCROLL","target":"s"})
print("construction_controls=9/9")
