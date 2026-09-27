import sqlite3, json
from pathlib import Path

POLICIES=("exact_version","predicate_truth")
SCENARIOS=("stable","semantic_same","predicate_invalid","unrelated_change")
REPS=50

def init_sender(path, cid):
    con=sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA synchronous=FULL")
    con.execute("CREATE TABLE outbox(command_id TEXT PRIMARY KEY, expected_version INTEGER, expected_allowed INTEGER, committed INTEGER)")
    con.execute("INSERT INTO outbox VALUES(?,?,?,1)",(cid,0,1))
    con.commit(); con.close()

def init_receiver(path):
    con=sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA synchronous=FULL")
    con.execute("CREATE TABLE context(id INTEGER PRIMARY KEY CHECK(id=1), target_version INTEGER, action_allowed INTEGER, unrelated_version INTEGER)")
    con.execute("INSERT INTO context VALUES(1,0,1,0)")
    con.execute("CREATE TABLE effects(command_id TEXT PRIMARY KEY, target_version INTEGER, action_allowed INTEGER, unrelated_version INTEGER)")
    con.execute("CREATE TABLE decisions(command_id TEXT PRIMARY KEY, policy TEXT, decision TEXT, reason TEXT, target_version INTEGER, action_allowed INTEGER, unrelated_version INTEGER)")
    con.commit(); con.close()

def mutate(path, scenario):
    con=sqlite3.connect(path); con.execute("BEGIN IMMEDIATE")
    if scenario=="semantic_same":
        con.execute("UPDATE context SET target_version=target_version+1 WHERE id=1")
    elif scenario=="predicate_invalid":
        con.execute("UPDATE context SET target_version=target_version+1, action_allowed=0 WHERE id=1")
    elif scenario=="unrelated_change":
        con.execute("UPDATE context SET unrelated_version=unrelated_version+1 WHERE id=1")
    elif scenario!="stable":
        raise ValueError(scenario)
    row=con.execute("SELECT target_version,action_allowed,unrelated_version FROM context WHERE id=1").fetchone()
    con.commit(); con.close()
    return {"target_version":row[0],"action_allowed":row[1],"unrelated_version":row[2]}

def dispatch(sender, receiver, policy):
    s=sqlite3.connect(sender)
    cmd=s.execute("SELECT command_id,expected_version,expected_allowed,committed FROM outbox").fetchone(); s.close()
    assert cmd[3]==1
    con=sqlite3.connect(receiver); con.execute("BEGIN IMMEDIATE")
    v,allowed,u=con.execute("SELECT target_version,action_allowed,unrelated_version FROM context WHERE id=1").fetchone()
    if policy=="exact_version":
        valid=(v==cmd[1]); reason="version_match" if valid else "version_changed"
    elif policy=="predicate_truth":
        valid=(allowed==cmd[2]); reason="predicate_match" if valid else "predicate_changed"
    else: raise ValueError(policy)
    decision="effect" if valid else "reject"
    if valid:
        con.execute("INSERT INTO effects VALUES(?,?,?,?)",(cmd[0],v,allowed,u))
    con.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?,?)",(cmd[0],policy,decision,reason,v,allowed,u))
    con.commit()
    n=con.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
    con.close()
    return {"decision":decision,"reason":reason,"effect_count":n,"target_version":v,"action_allowed":allowed,"unrelated_version":u}

def run_case(root,policy,scenario,rep):
    cid=f"{policy}-{scenario}-{rep:03d}"
    d=Path(root)/cid; d.mkdir(parents=True)
    sender=d/"sender.sqlite"; receiver=d/"receiver.sqlite"
    init_sender(sender,cid); init_receiver(receiver)
    pre=mutate(receiver,scenario); delivery=dispatch(sender,receiver,policy)
    row={"case_id":cid,"policy":policy,"scenario":scenario,"rep":rep,"pre_delivery_context":pre,"delivery":delivery,"sender_committed":True}
    (d/"record.json").write_text(json.dumps(row,sort_keys=True,indent=2))
    return row

def run_all(root):
    rows=[]
    for p in POLICIES:
        for s in SCENARIOS:
            for r in range(REPS):
                rows.append(run_case(root,p,s,r))
    (Path(root)/"records.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
    return rows
