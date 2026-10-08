from contract import GAP_NS,REALIZE_NS,LOCAL_COST_NS

def select_current(history):
    return {1}

def select_temporal(history):
    a,b,c=history
    if a<b and b<c:return {1}
    if a>b and b>c:return {-1}
    return {1}

def expected(prepared,realized,authority=True,expired=False):
    hit=bool(authority and not expired and realized in prepared)
    latency=LOCAL_COST_NS if hit else GAP_NS-REALIZE_NS+LOCAL_COST_NS
    return hit,latency
