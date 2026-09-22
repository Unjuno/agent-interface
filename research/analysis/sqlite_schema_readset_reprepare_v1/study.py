import argparse, json, os, pathlib, sqlite3, subprocess, sys, time, hashlib, shutil

SOURCE_FILES=('study.py','audit.py','corruption.py','manifest.py','PLAN.md','ENVIRONMENT.json','FREEZE.json')
POLICIES = ('STALE_METADATA','LIFETIME_UNION','SCHEMA_SCOPED_REPLACE')
SCENARIOS = (
    'STABLE_A_NONE',
    'RETARGET_B_NONE',
    'RETARGET_B_MUTATE_B',
    'RETARGET_B_MUTATE_A',
    'UNRELATED_SCHEMA_A_MUTATE_A',
    'UNRELATED_SCHEMA_A_MUTATE_B',
    'RETARGET_B_EXECUTE_BACK_A_MUTATE_B',
    'RETARGET_B_EXECUTE_BACK_A_MUTATE_A',
)
BASE_TABLES={'a','b'}

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20), b''): h.update(chunk)
    return h.hexdigest()

def schema_version(conn):
    return int(conn.execute('PRAGMA schema_version').fetchone()[0])

def setup_db(path):
    c=sqlite3.connect(path)
    c.executescript('''
    PRAGMA journal_mode=DELETE;
    PRAGMA synchronous=FULL;
    CREATE TABLE a(value TEXT NOT NULL, revision INTEGER NOT NULL);
    CREATE TABLE b(value TEXT NOT NULL, revision INTEGER NOT NULL);
    CREATE TABLE effects(id INTEGER PRIMARY KEY, value TEXT NOT NULL, policy TEXT NOT NULL, scenario TEXT NOT NULL, rep INTEGER NOT NULL);
    INSERT INTO a VALUES('A1',1);
    INSERT INTO b VALUES('B1',1);
    CREATE VIEW v_dep AS SELECT value, revision FROM a;
    ''')
    c.commit(); c.close()

def retarget(conn, table):
    conn.execute('DROP VIEW v_dep')
    conn.execute(f'CREATE VIEW v_dep AS SELECT value, revision FROM {table}')
    conn.commit()

def mutate(path, table):
    c=sqlite3.connect(path)
    c.execute('BEGIN IMMEDIATE')
    c.execute(f"UPDATE {table} SET value=value||'x', revision=revision+1")
    c.commit(); c.close()

def read_revisions(path, deps):
    c=sqlite3.connect(path)
    out={}
    for dep in sorted(deps):
        out[dep]=int(c.execute(f'SELECT revision FROM {dep}').fetchone()[0])
    c.close(); return out

class Tracker:
    def __init__(self):
        self.events=[]
        self.current=[]
    def begin(self, phase):
        self.phase=phase; self.current=[]
    def callback(self, action,arg1,arg2,dbname,source):
        if action==sqlite3.SQLITE_READ:
            row={'phase':self.phase,'table':arg1,'column':arg2,'db':dbname,'source':source}
            self.events.append(row); self.current.append(row)
        return sqlite3.SQLITE_OK
    def base_reads(self):
        return {r['table'] for r in self.current if r['table'] in BASE_TABLES}

def policy_execute(conn, tracker, policy, state, phase):
    sv_before=schema_version(conn)
    if policy=='SCHEMA_SCOPED_REPLACE' and state['schema_version'] != sv_before:
        state['deps']=set()
    tracker.begin(phase)
    row=conn.execute('SELECT value, revision FROM v_dep').fetchone()
    reads=tracker.base_reads()
    if policy=='LIFETIME_UNION':
        state['deps'] |= reads
    elif policy=='SCHEMA_SCOPED_REPLACE':
        if reads:
            state['deps'] |= reads
    elif policy=='STALE_METADATA':
        if not state['deps']:
            state['deps'] |= reads
    else:
        raise ValueError(policy)
    state['schema_version']=sv_before
    return {'value':row[0],'revision':int(row[1]),'schema_version':sv_before,'callbacks':sorted(reads)}

def apply_pre_schema(conn, tracker, policy, state, scenario):
    target='a'
    history=[]
    if scenario.startswith('RETARGET_B_'):
        retarget(conn,'b'); target='b'; history.append({'op':'retarget','target':'b','schema_version':schema_version(conn)})
    elif scenario.startswith('UNRELATED_SCHEMA_A_'):
        conn.execute('CREATE TABLE junk(x INTEGER)'); conn.commit(); history.append({'op':'unrelated_schema','schema_version':schema_version(conn)})
    if scenario.startswith('RETARGET_B_EXECUTE_BACK_A_'):
        mid=policy_execute(conn,tracker,policy,state,'intermediate_b')
        history.append({'op':'intermediate_execute','row':mid,'deps_after':sorted(state['deps'])})
        retarget(conn,'a'); target='a'; history.append({'op':'retarget','target':'a','schema_version':schema_version(conn)})
    return target,history

def scenario_mutation(s):
    if s.endswith('_MUTATE_A'): return 'a'
    if s.endswith('_MUTATE_B'): return 'b'
    return None

def validate_and_effect(path, deps, prepared_revs, prepared_value, policy, scenario, rep):
    c=sqlite3.connect(path)
    c.execute('BEGIN IMMEDIATE')
    current={}
    ok=True
    for dep in sorted(deps):
        rv=int(c.execute(f'SELECT revision FROM {dep}').fetchone()[0]); current[dep]=rv
        if rv != prepared_revs[dep]: ok=False
    if ok:
        c.execute('INSERT INTO effects(value,policy,scenario,rep) VALUES(?,?,?,?)',(prepared_value,policy,scenario,rep))
    c.commit(); c.close()
    return ok,current

def run_case(policy,scenario,rep,outdir):
    out=pathlib.Path(outdir); out.mkdir(parents=True,exist_ok=False)
    db=out/'case.db'; setup_db(db)
    conn=sqlite3.connect(db, cached_statements=128)
    tracker=Tracker(); conn.set_authorizer(tracker.callback)
    state={'deps':set(),'schema_version':None}
    warm=policy_execute(conn,tracker,policy,state,'warm_a')
    initial={'schema_version':state['schema_version'],'deps':sorted(state['deps']),'row':warm}
    target,history=apply_pre_schema(conn,tracker,policy,state,scenario)
    prepared=policy_execute(conn,tracker,policy,state,'final_prepare')
    deps=set(state['deps'])
    prepared_revs=read_revisions(db,deps)
    conn.close()
    mutation=scenario_mutation(scenario)
    if mutation: mutate(db,mutation)
    accepted,current_revs=validate_and_effect(db,deps,prepared_revs,prepared['value'],policy,scenario,rep)
    c=sqlite3.connect(db)
    effects=c.execute('SELECT id,value,policy,scenario,rep FROM effects ORDER BY id').fetchall()
    final_tables={t:{'value':c.execute(f'SELECT value FROM {t}').fetchone()[0], 'revision':int(c.execute(f'SELECT revision FROM {t}').fetchone()[0])} for t in ('a','b')}
    final_sv=schema_version(c); c.close()
    row={
      'policy':policy,'scenario':scenario,'rep':rep,'target':target,'mutation':mutation,
      'initial':initial,'schema_history':history,'prepared':prepared,'deps':sorted(deps),
      'prepared_revisions':prepared_revs,'current_revisions_at_validation':current_revs,
      'accepted':accepted,'effects':[list(x) for x in effects],'final_tables':final_tables,
      'final_schema_version':final_sv,'authorizer_events':tracker.events,
    }
    (out/'CASE.json').write_text(json.dumps(row,indent=2,sort_keys=True))
    return row

def formal(root):
    root=pathlib.Path(root); root.mkdir(parents=True,exist_ok=False)
    snap=root/'source_snapshot'; snap.mkdir()
    srcdir=pathlib.Path(__file__).resolve().parent
    for name in SOURCE_FILES:
        shutil.copyfile(srcdir/name, snap/name)
    rows=[]; idx=0
    for rep in range(2):
      for scenario in SCENARIOS:
       for policy in POLICIES:
        cid=f'{idx:03d}_{policy}_{scenario}_r{rep}'
        cdir=root/cid
        cmd=[sys.executable, str(pathlib.Path(__file__).resolve()), '--case', policy, scenario, str(rep), str(cdir)]
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
        (cdir/'stdout.txt').write_text(cp.stdout)
        (cdir/'stderr.txt').write_text(cp.stderr)
        exitrec={'returncode':cp.returncode,'cmd':cmd}
        (cdir/'EXIT.json').write_text(json.dumps(exitrec,indent=2))
        if cp.returncode!=0: raise RuntimeError(f'case failed {cid}')
        row=json.loads((cdir/'CASE.json').read_text()); row['case_id']=cid; rows.append(row); idx+=1
    (root/'RAW.json').write_text(json.dumps({'rows':rows,'case_count':len(rows),'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0},indent=2,sort_keys=True))
    print(json.dumps({'case_count':len(rows),'root':str(root)},sort_keys=True))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--case',nargs=4); ap.add_argument('--formal')
    a=ap.parse_args()
    if a.case:
        p,s,r,o=a.case
        print(json.dumps(run_case(p,s,int(r),o),sort_keys=True))
    elif a.formal: formal(a.formal)
    else: ap.error('mode required')
