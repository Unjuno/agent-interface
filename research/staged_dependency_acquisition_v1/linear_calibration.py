import hashlib, sqlite3, statistics, time, json, platform
from pathlib import Path
KS=[1,2,4,8,10]
REPS=4000
keys=[f'k{i}' for i in range(10)]
blobs={k:hashlib.sha256(k.encode()).digest()*512 for k in keys}
def med(fn,n=REPS):
    vals=[]
    for _ in range(n):
        t=time.perf_counter_ns();fn();vals.append(time.perf_counter_ns()-t)
    return statistics.median(vals)/1000
def fit(points):
    xs=[x for x,y in points];ys=[y for x,y in points]
    xm=statistics.fmean(xs);ym=statistics.fmean(ys)
    den=sum((x-xm)**2 for x in xs)
    b=sum((x-xm)*(y-ym) for x,y in points)/den
    a=ym-b*xm
    return a,b
def heavy(n):
    x=0
    for k in keys[:n]:x ^= hashlib.sha256(blobs[k]).digest()[0]
    return x
for _ in range(100):heavy(10)
heavy_points=[(k,med(lambda k=k:heavy(k))) for k in KS]
ha,hb=fit(heavy_points)
con=sqlite3.connect(':memory:');con.execute('create table d(k text primary key,v text)');con.executemany('insert into d values(?,?)',[(k,k*8) for k in keys]);con.commit()
def q(n):
    qx='select v from d where k in ('+','.join('?'*n)+')';return con.execute(qx,keys[:n]).fetchall()
for _ in range(100):q(10)
sql_points=[(k,med(lambda k=k:q(k))) for k in KS]
sa,sb=fit(sql_points)
case={'pre':2,'selected':4,'inactive':4}
def decision(a,b):
    union=a+b*10; staged=2*a+b*6
    return {'pred_union_us':union,'pred_staged_us':staged,'selected':'staged' if staged<union else 'union'}
def heavy_union():return heavy(10)
def heavy_staged():return heavy(2),heavy(4)
def sql_union():return q(10)
def sql_staged():return q(2),q(4)
summary={'schema':'dependency-cost-calibration-v1','environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.platform()},'reps':REPS,'case':case,
'heavy':{'points':heavy_points,'fit_fixed_us':ha,'fit_per_dep_us':hb,'prediction':decision(ha,hb),'actual_union_us':med(heavy_union),'actual_staged_us':med(heavy_staged)},
'sqlite':{'points':sql_points,'fit_fixed_us':sa,'fit_per_dep_us':sb,'prediction':decision(sa,sb),'actual_union_us':med(sql_union),'actual_staged_us':med(sql_staged)}}
summary['heavy']['actual_winner']='staged' if summary['heavy']['actual_staged_us']<summary['heavy']['actual_union_us'] else 'union'
summary['sqlite']['actual_winner']='staged' if summary['sqlite']['actual_staged_us']<summary['sqlite']['actual_union_us'] else 'union'
summary['prediction_matches_actual']=summary['heavy']['prediction']['selected']==summary['heavy']['actual_winner'] and summary['sqlite']['prediction']['selected']==summary['sqlite']['actual_winner']
Path(__file__).with_name('summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
