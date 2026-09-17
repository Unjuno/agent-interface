from __future__ import annotations
import random

CLASSES = ["EXTERNAL_PROCESS", "HUMAN", "OS", "THIS_SESSION_OTHER_INTENT"]

def base_record(i, mutation=True, dt=100):
    return {
        "record_id": f"r{i:06d}",
        "session_id": f"s{i%97}",
        "intent_id": f"i{i%211}",
        "action_id": f"a{i}",
        "target_id": f"t{i%401}",
        "delta_kind": ["VALUE", "GEOMETRY", "VISIBILITY", "SELECTION"][i%4],
        "action_time_ms": 1000000 + i*3,
        "mutation_time_ms": 1000000 + i*3 + dt,
        "mutation": mutation,
        "witnesses": [],
    }

def exact_self(i, dt=100):
    r=base_record(i, True, dt)
    r["witnesses"]=[{k:r[k] for k in ("session_id","intent_id","action_id","target_id","delta_kind")} | {"actor_class":"THIS_INTENT","time_ms":r["mutation_time_ms"]}]
    return r

def external(i, cls, dt=100):
    r=base_record(i, True, dt)
    w={"actor_class":cls,"time_ms":r["mutation_time_ms"],"target_id":r["target_id"],"delta_kind":r["delta_kind"]}
    if cls=="THIS_SESSION_OTHER_INTENT":
        w.update(session_id=r["session_id"], intent_id=r["intent_id"]+"x", action_id=r["action_id"]+"x")
    r["witnesses"]=[w]
    return r

def unattributed(i, mode, dt=100):
    r=base_record(i, True, dt)
    if mode==0:
        pass
    elif mode==1:
        w={k:r[k] for k in ("session_id","intent_id","action_id","target_id","delta_kind")}
        w.update(actor_class="THIS_INTENT",time_ms=r["mutation_time_ms"],target_id=r["target_id"]+"x")
        r["witnesses"]=[w]
    elif mode==2:
        s={k:r[k] for k in ("session_id","intent_id","action_id","target_id","delta_kind")}
        s.update(actor_class="THIS_INTENT",time_ms=r["mutation_time_ms"])
        h={"actor_class":"HUMAN","time_ms":r["mutation_time_ms"],"target_id":r["target_id"],"delta_kind":r["delta_kind"]}
        r["witnesses"]=[s,h]
    elif mode==3:
        r["witnesses"]=[{"actor_class":"UNKNOWN","time_ms":r["mutation_time_ms"]}]
    elif mode==4:
        r["witnesses"]=[{"actor_class":"ALIEN","time_ms":r["mutation_time_ms"]}]
    elif mode==5:
        s={k:r[k] for k in ("session_id","intent_id","action_id","target_id","delta_kind")}
        s.update(actor_class="THIS_INTENT",time_ms=r["action_time_ms"]-1)
        r["witnesses"]=[s]
    return r

def formal_records(seed=121120260918001, per_stratum=80000):
    rng=random.Random(seed)
    rows=[]; n=per_stratum
    for j in range(n):
        rows.append(("self", exact_self(j,rng.randint(0,1500))))
    off=n
    for j in range(n):
        rows.append(("external",external(off+j,CLASSES[rng.randrange(len(CLASSES))],rng.randint(0,900))))
    off+=n
    for j in range(n):
        rows.append(("unattributed",unattributed(off+j,rng.randrange(6),rng.randint(0,900))))
    off+=n
    for j in range(n):
        r=base_record(off+j,False,0); r["mutation_time_ms"]=r["action_time_ms"]; rows.append(("no_mutation",r))
    rng.shuffle(rows)
    return rows
