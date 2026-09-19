import hashlib, json

def digest(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(raw).hexdigest(), raw

def main():
    source={'frame':'A1','region':[1,1,2,2],'pixels':[[2]]}
    h,raw=digest(source)
    controls=[]
    for key,value in [('frame','B1'),('region',[0,0,2,2]),('pixels',[[3]]),('extra',True)]:
        altered=dict(source); altered[key]=value
        h2,_=digest(altered)
        controls.append(h2 != h)
    truncated=raw[:-1]
    try:
        json.loads(truncated)
        parsed=False
    except json.JSONDecodeError:
        parsed=True
    assert all(controls) and parsed
    print({'tamper_controls':len(controls),'digest_changes':sum(controls),'truncation_rejected':parsed})

if __name__ == '__main__': main()

