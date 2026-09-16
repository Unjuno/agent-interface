HORIZON_NS = 50_000_000
ORIGINS_NS = [10**12 + 123, 10**15 + 123, 3*10**15 + 123, 10**16 + 123]
TRACES = [
    {'name':'positive_velocity_jitter','intervals_ns':[16_000_000,17_300_000,15_800_000,18_100_000,16_600_000],'velocity':137.0,'intercept':23.0},
    {'name':'negative_velocity_jitter','intervals_ns':[11_100_001,21_777_777,13_333_337,19_999_991,17_123_457],'velocity':-83.5,'intercept':500.0},
    {'name':'slow_velocity_jitter','intervals_ns':[7_000_003,23_000_009,9_000_007,31_000_011,12_000_013],'velocity':0.125,'intercept':1.0},
    {'name':'static','intervals_ns':[13_111_111,18_222_223,14_333_337,21_444_449,17_555_557],'velocity':0.0,'intercept':42.0},
]
POLICIES = ['absolute_float_seconds','origin_shifted_delta_seconds']

def materialize(trace, origin_ns):
    ts=[origin_ns]
    for d in trace['intervals_ns']:
        ts.append(ts[-1]+d)
    v=trace['velocity']; x0=trace['intercept']
    xs=[x0 + v*((t-origin_ns)/1_000_000_000.0) for t in ts]
    truth=x0 + v*((ts[-1]+HORIZON_NS-origin_ns)/1_000_000_000.0)
    return ts,xs,truth

def formal_cases():
    out=[]
    i=0
    for trace in TRACES:
        for origin in ORIGINS_NS:
            for policy in POLICIES:
                i+=1
                out.append({'case_id':f'm{i:02d}','trace':trace,'origin_ns':origin,'policy':policy})
    return out
