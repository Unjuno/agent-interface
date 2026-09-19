import random
from baseline import Case

SAMPLE_NAMES={"sample_pre","sample_post"}

def strip_samples(trace):
    return [row for row in trace if row[0] not in SAMPLE_NAMES]

def state_tuple(s):
    return (s.revision,s.active_relation,s.active_pointer,s.held_relation,s.touched,s.physical_down)

def make_case(rng):
    return Case(
        op=rng.choice(["down","up"]),
        key_available=rng.random()<0.98,
        fault=rng.random()<0.05,
        active_relation=rng.choice(["none","self","other"]),
        focus_invalid=rng.random()<0.08,
        lease_ok=rng.random()<0.94,
        cancel=rng.random()<0.07,
        held_relation=rng.choice(["none","self","other"]),
        physical_down=rng.choice([False,True]),
        inject_ok=rng.random()<0.97,
        sync_ok=rng.random()<0.97,
        sample_pre_ok=rng.random()<0.90,
        sample_post_ok=rng.random()<0.90,
    )

def fixed_cases():
    B=dict(key_available=True,fault=False,active_relation="none",focus_invalid=False,lease_ok=True,cancel=False,held_relation="none",physical_down=False,inject_ok=True,sync_ok=True,sample_pre_ok=True,sample_post_ok=True)
    out=[]
    def add(name,op,**kw):
        d=dict(B); d.update(kw); d["op"]=op; out.append((name,Case(**d)))
    add("down_clean","down")
    add("down_preexisting_physical","down",physical_down=True)
    add("down_sample_pre_fail","down",sample_pre_ok=False)
    add("down_sample_post_fail","down",sample_post_ok=False)
    add("down_focus_reject","down",focus_invalid=True)
    add("down_cancel_reject","down",cancel=True)
    add("down_inject_fail","down",inject_ok=False)
    add("down_sync_fail","down",sync_ok=False)
    add("up_held_clean","up",held_relation="self",physical_down=True)
    add("up_held_already_physical_up","up",held_relation="self",physical_down=False)
    add("up_noop_up","up",held_relation="none",physical_down=False)
    add("up_noop_physical_down","up",held_relation="none",physical_down=True)
    add("up_sample_pre_fail","up",held_relation="self",physical_down=True,sample_pre_ok=False)
    add("up_sample_post_fail","up",held_relation="self",physical_down=True,sample_post_ok=False)
    add("up_foreign_reject","up",held_relation="other",physical_down=True)
    add("up_inject_fail","up",held_relation="self",physical_down=True,inject_ok=False)
    add("up_sync_fail","up",held_relation="self",physical_down=True,sync_ok=False)
    add("key_unavailable_down","down",key_available=False)
    add("key_unavailable_up","up",key_available=False)
    return out
