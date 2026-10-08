import sqlite3, json
from pathlib import Path

POLICIES=("id_plus_predicate","generation_plus_predicate")
SCENARIOS=("stable","same_id_replaced","predicate_invalid","unrelated_change")
REPS=50

def init_sender(path,cid):
    con=sqlite3.connect(path); con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA synchronous=FULL")
    con.execute("CREATE TABLE outbox(command_id TEXT PRIMARY KEY, expected_context TEXT, expected_generation INTEGER, expected_allowed INTEGER, committed INTEGER)")
    con.execute("INSERT INTO outbox VALUES(?,?,?,?,1)",(cid,"A",0,1)); con.commit(); con.close()

def init_receiver(path):
    con=sqlite3.connect(path); con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA synchronous=FULL")
    con.execute("CREATE TABLE context(id INTEGER PRIMARY KEY CHECK(id=1), context_id TEXT, generation INTEGER, action_allowed INTEGER, unrelated_version INTEGER)")
    con.execute("INSERT INTO context VALUES(1,'A',0,1,0)")
    con.execute("CREATE TABLE effects(command_id TEXT PRIMARY KEY, context_id TEXT, generation INTEGER, action_allowed INTEGER, unrelated_version INTEGER)")
    con.execute("CREATE TABLE decisions(command_id TEXT PRIMARY KEY, policy TEXT, decision TEXT, reason TEXT, context_id TEXT, generation INTEGER, action_allowed INTEGER, unrelated_version INTEGER)")
    con.commit(); con.close()

def mutate(path,scenario):
    con=sqlite3.connect(path); con.execute("BEGIN IMMEDIATE")
    if scenario=="same_id_replaced": con.execute("UPDATE context SET generation=generation+1 WHERE id=1")
    elif scenario=="predicate_invalid": con.execute("UPDATE context SET action_allowed=0 WHERE id=1")
    elif scenario=="unrelated_change": con.execute("UPDATE context SET unrelated_version=unrelated_version+1 WHERE id=1")
    elif scenario!="stable": raise ValueError(scenario)
    r=con.execute("SELECT context_id,generation,action_allowed,unrelated_version FROM context").fetchone(); con.commit(); con.close()
    return {"context_id":r[0],"generation":r[1],"action_allowed":r[2],"unrelated_version":r[3]}

def dispatch(sender,receiver,policy):
    s=sqlite3.connect(sender); cmd=s.execute("SELECT command_id,expected_context,expected_generation,expected_allowed,committed FROM outbox").fetchone(); s.close(); assert cmd[4]==1
    con=sqlite3.connect(receiver); con.execute("BEGIN IMMEDIATE")
    ctx,gen,allowed,u=con.execute("SELECT context_id,generation,action_allowed,unrelated_version FROM context").fetchone()
    if policy=="id_plus_predicate":
        valid=(ctx==cmd[1] and allowed==cmd[3]); reason="id_predicate_match" if valid else ("id_changed" if ctx!=cmd[1] else "predicate_changed")
    elif policy=="generation_plus_predicate":
        valid=(ctx==cmd[1] and gen==cmd[2] and allowed==cmd[3]); reason="generation_predicate_match" if valid else ("id_changed" if ctx!=cmd[1] else ("generation_changed" if gen!=cmd[2] else "predicate_changed"))
    else: raise ValueError(policy)
    decision="effect" if valid else "reject"
    if valid: con.execute("INSERT INTO effects VALUES(?,?,?,?,?)",(cmd[0],ctx,gen,allowed,u))
    con.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?,?,?)",(cmd[0],policy,decision,reason,ctx,gen,allowed,u)); con.commit()
    n=con.execute("SELECT COUNT(*) FROM effects").fetchone()[0]; con.close()
    return {"decision":decision,"reason":reason,"effect_count":n,"context_id":ctx,"generation":gen,"action_allowed":allowed,"unrelated_version":u}

def run_case(root,p,s,r):
    cid=f"{p}-{s}-{r:03d}"; d=Path(root)/cid; d.mkdir(parents=True)
    sender=d/"sender.sqlite"; receiver=d/"receiver.sqlite"; init_sender(sender,cid); init_receiver(receiver)
    pre=mutate(receiver,s); delivery=dispatch(sender,receiver,p)
    row={"case_id":cid,"policy":p,"scenario":s,"rep":r,"pre_delivery_context":pre,"delivery":delivery,"sender_committed":True}
    (d/"record.json").write_text(json.dumps(row,sort_keys=True,indent=2)); return row

def run_all(root):
    rows=[]
    for p in POLICIES:
        for s in SCENARIOS:
            for r in range(REPS): rows.append(run_case(root,p,s,r))
    (Path(root)/"records.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows)); return rows
