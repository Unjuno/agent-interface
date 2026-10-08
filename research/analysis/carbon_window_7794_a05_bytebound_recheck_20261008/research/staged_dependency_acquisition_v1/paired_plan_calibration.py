import hashlib, sqlite3, statistics, time, json, platform
from pathlib import Path
keys=[f'k{i}' for i in range(10)]
blobs={k:hashlib.sha256(k.encode()).digest()*512 for k in keys}
def heavy(n):
    x=0
    for k in keys[:n]:x ^= hashlib.sha256(blobs[k]).digest()[0]
    return x
con=sqlite3.connect(':memory:');con.execute('create table d(k text primary key,v text)');con.executemany('insert into d values(?,?)',[(k,k*8) for k in keys]);con.commit()
def q(n):
    s='select v from d where k in ('+','.join('?'*n)+')';return con.execute(s,keys[:n]).fetchall()
backends={'heavy':(lambda:heavy(10),lambda:(heavy(2),heavy(4))),'sqlite':(lambda:q(10),lambda:(q(2),q(4)))}
def sample(fn,n):
    vals=[]
    for _ in range(n):
        t=time.perf_counter_ns();fn();vals.append(time.perf_counter_ns()-t)
    return vals
for u,s in backends.values():
    for _ in range(100):u();s()
holdout={}
for name,(u,s) in backends.items():
    um=statistics.median(sample(u,5000));sm=statistics.median(sample(s,5000))
    holdout[name]={'union_median_us':um/1000,'staged_median_us':sm/1000,'winner':'union' if um<sm else 'staged'}
results={}
for ncal in [10,20,50,100,200,500]:
    results[str(ncal)]={}
    for name,(u,s) in backends.items():
        correct=0;choices={'union':0,'staged':0}
        for block in range(20):
            if block%2==0:
                um=statistics.median(sample(u,ncal));sm=statistics.median(sample(s,ncal))
            else:
                sm=statistics.median(sample(s,ncal));um=statistics.median(sample(u,ncal))
            choice='union' if um<sm else 'staged'; choices[choice]+=1
            correct += choice==holdout[name]['winner']
        results[str(ncal)][name]={'correct_blocks':correct,'blocks':20,'choices':choices}
summary={'schema':'dependency-plan-calibration-v1','environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.platform()},'holdout':holdout,'calibration':results}
Path(__file__).with_name('summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
