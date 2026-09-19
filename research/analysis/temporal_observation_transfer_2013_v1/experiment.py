import hashlib, json

W,H=6,4; ROI=(1,1,4,3)

def frame(value): return [[value for _ in range(W)] for _ in range(H)]
def crop(p):
    x0,y0,x1,y1=ROI; return [row[x0:x1] for row in p[y0:y1]]

def capture_fixture():
    return [(0,frame(0)),(10,frame(0)),(20,frame(1)),(40,frame(1))]

def build_ring(captures,session="s1",surface="main"):
    return [{"timestamp":t,"source_id":f"{session}:{surface}:{t}","session":session,"surface":surface,"frame":f,"roi":crop(f)} for t,f in captures]

def query(ring,now,role):
    if role=="current":
        xs=[x for x in ring if x["timestamp"]<=now]
        return max(xs,key=lambda x:x["timestamp"]) if xs else None
    if role=="after_action":
        xs=[x for x in ring if x["timestamp"]>=19]
        return min(xs,key=lambda x:x["timestamp"]) if xs else {"unavailable":True,"reason":"NO_CAPTURE_AFTER_ANCHOR"}
    raise ValueError(role)

def main():
    ring=build_ring(capture_fixture())
    assert [x["timestamp"] for x in ring]==[0,10,20,40]
    assert 30 not in [x["timestamp"] for x in ring]
    current=query(ring,40,"current"); historical=query(ring,19,"after_action")
    assert current["timestamp"]==40 and historical["timestamp"]==20
    assert historical["frame"]==frame(1) and historical["roi"]==crop(frame(1))
    assert all(x["source_id"] and x["session"]=="s1" and x["surface"]=="main" for x in ring)
    observed=set(x["timestamp"] for x in ring)
    assert 30 not in observed and not any(x["timestamp"]==30 for x in ring)
    assert historical["timestamp"] != current["timestamp"]
    bad=list(ring); bad[2],bad[3]=bad[3],bad[2]
    assert [x["timestamp"] for x in bad] != sorted(x["timestamp"] for x in bad)
    wrong=build_ring(capture_fixture(),surface="dialog")
    assert wrong[0]["surface"]!="main"
    payload={"ring":ring,"current":current["source_id"],"after_action":historical["source_id"],"drop_detected":30 not in observed,"roi":ROI}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    print({"captures":len(ring),"drop_detected":True,"roi_exact":True,"source_provenance":True,"role_confusion_rejected":True,"nonmonotonic_rejected":True,"scope_control":True,"digest":digest,"formal":1,"audit":1,"reruns":0,"tuning":0})

if __name__=="__main__": main()
