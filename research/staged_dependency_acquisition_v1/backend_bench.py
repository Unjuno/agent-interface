import hashlib, sqlite3, statistics, time, json, random, platform
from pathlib import Path
PRE=['p0','p1']; SEL=['s0','s1','s2','s3']; INACT=['i0','i1','i2','i3']; UNION=PRE+SEL+INACT
N_HASH=5000; N_SQL=10000
rng=random.Random(202609160227)
blobs={k:hashlib.sha256(k.encode()).digest()*512 for k in UNION}

def heavy(keys):
    out=0
    for k in keys:
        out ^= hashlib.sha256(blobs[k]).digest()[0]
    return out

def time_ns(fn,n):
    vals=[]
    for _ in range(n):
        t=time.perf_counter_ns(); fn(); vals.append(time.perf_counter_ns()-t)
    return vals
for _ in range(100): heavy(UNION); heavy(PRE); heavy(SEL)
h_union=time_ns(lambda: heavy(UNION),N_HASH)
h_staged=time_ns(lambda:(heavy(PRE),heavy(SEL)),N_HASH)
con=sqlite3.connect(':memory:')
con.execute('create table d(k text primary key, v text)')
con.executemany('insert into d values(?,?)',[(k,k*8) for k in UNION]); con.commit()
def query(keys):
    q='select v from d where k in ('+','.join('?'*len(keys))+')'
    return con.execute(q,keys).fetchall()
for _ in range(100):query(UNION);query(PRE);query(SEL)
s_union=time_ns(lambda:query(UNION),N_SQL)
s_staged=time_ns(lambda:(query(PRE),query(SEL)),N_SQL)
def stats(v):
    s=sorted(v);return {'median_us':statistics.median(v)/1000,'p95_us':s[int(.95*(len(s)-1))]/1000,'mean_us':statistics.fmean(v)/1000}
summary={'schema':'dependency-backend-cost-v1','environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.platform()},
'case':{'pre':2,'selected':4,'inactive':4},
'heavy_hash':{'iterations':N_HASH,'union':stats(h_union),'staged':stats(h_staged)},
'sqlite_scalar':{'iterations':N_SQL,'union':stats(s_union),'staged':stats(s_staged)}}
for name in ['heavy_hash','sqlite_scalar']:
    summary[name]['median_staged_vs_union_pct']=100*(summary[name]['staged']['median_us']-summary[name]['union']['median_us'])/summary[name]['union']['median_us']
Path(__file__).with_name('summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
