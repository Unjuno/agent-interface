"""Finite GUI-like micro-change gate successor for Issue #2001."""
import hashlib,json
W,H=32,16
def img(changes=()):
    a=[0]*(W*H)
    for x,y,w,h,v in changes:
        for yy in range(y,y+h):
            for xx in range(x,x+w): a[yy*W+xx]=v
    return bytes(a)
def ahash(a):
    m=sum(a)/len(a)
    return tuple(v>=m for v in a)
CASES=[
 ("unchanged",img(),img(),False,False),
 ("noise",img(),img(((2,2,1,1,255),)),False,False),
 ("task_micro",img(),img(((10,6,1,1,255),)),True,True),
 ("task_large",img(),img(((10,6,5,4,255),)),True,True),
 ("panel",img(((0,0,16,16,120),)),img(((0,0,16,16,200),)),True,True),
 ("unchanged_panel",img(((0,0,16,16,120),)),img(((0,0,16,16,120),)),False,False)]
def run():
    rows=[]
    for name,a,b,relevant,changed in CASES:
        same=ahash(a)==ahash(b); exact=a==b
        rows.append({"name":name,"hash_same":same,"exact_same":exact,
                     "task_relevant":relevant,"changed":changed,
                     "fallback_forward":same and not exact})
    return rows
if __name__=="__main__":
    rows=run()
    assert any(r["task_relevant"] and r["hash_same"] and not r["exact_same"] for r in rows)
    assert all((not r["fallback_forward"]) or not r["exact_same"] for r in rows)
    print("cases",len(rows),"task_false_suppression",
          sum(r["task_relevant"] and r["hash_same"] and not r["exact_same"] for r in rows),
          "fallback_catches",sum(r["fallback_forward"] for r in rows))
    print("digest",hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())
