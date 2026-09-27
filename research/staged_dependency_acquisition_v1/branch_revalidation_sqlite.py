import sqlite3, tempfile, json, time, statistics, platform
from pathlib import Path
N=100
methods=['union_phase2','staged_no_branch_revalidate','staged_revalidate']
mutations=['stable','inactive_guard','selected_guard','mode_flip','unrelated']
counts={m:{mu:{'correct':0,'wrong':0} for mu in mutations} for m in methods}
times={m:[] for m in methods}
with tempfile.TemporaryDirectory() as td:
    db=Path(td)/'x.db'
    con=sqlite3.connect(db);con.execute('pragma journal_mode=WAL');con.execute('create table s(k text primary key,v text)');con.execute('create table effects(action text)');con.close()
    for rep in range(N):
      for mu in mutations:
       for method in methods:
        c=sqlite3.connect(db,isolation_level=None,timeout=1)
        c.execute('delete from s');c.execute('delete from effects');c.executemany('insert into s values(?,?)',[('mode','A'),('gA','1'),('gB','1'),('noise','0')])
        selected=c.execute("select v from s where k='mode'").fetchone()[0]
        assert selected=='A'
        if mu=='inactive_guard':c.execute("update s set v='0' where k='gB'")
        elif mu=='selected_guard':c.execute("update s set v='0' where k='gA'")
        elif mu=='mode_flip':c.execute("update s set v='B' where k='mode'")
        elif mu=='unrelated':c.execute("update s set v='1' where k='noise'")
        t=time.perf_counter_ns();c.execute('begin immediate')
        vals=dict(c.execute("select k,v from s").fetchall())
        if method=='union_phase2': ok=vals['mode']==selected and vals['gA']=='1' and vals['gB']=='1'
        elif method=='staged_no_branch_revalidate': ok=vals['gA']=='1'
        else: ok=vals['mode']==selected and vals['gA']=='1'
        if ok:c.execute("insert into effects values('A')")
        c.execute('commit');times[method].append(time.perf_counter_ns()-t)
        valid=vals['mode']=='A' and vals['gA']=='1'
        effect=c.execute('select count(*) from effects').fetchone()[0]==1
        right=(effect==valid)
        counts[method][mu]['correct' if right else 'wrong']+=1
        c.close()
summary={'schema':'staged-branch-revalidation-sqlite-v1','repetitions':N,'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.platform()},'results':counts,'timing':{m:{'median_us':statistics.median(v)/1000,'p95_us':sorted(v)[int(.95*(len(v)-1))]/1000} for m,v in times.items()}}
assert counts['staged_revalidate']['mode_flip']['wrong']==0 and counts['staged_revalidate']['inactive_guard']['wrong']==0
assert counts['staged_no_branch_revalidate']['mode_flip']['wrong']==N
assert counts['union_phase2']['inactive_guard']['wrong']==N
Path(__file__).with_name('branch_revalidation_sqlite_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
