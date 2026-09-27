#!/usr/bin/env python3
"""Independent raw-only reconstruction; intentionally does not import runner.py."""
import hashlib, json, pathlib, sqlite3, sys

def ro_count(path, table):
    if not path.exists(): return 0
    db=sqlite3.connect(f"file:{path}?mode=ro",uri=True); db.execute("PRAGMA query_only=ON")
    try: value=db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError: value=0
    db.close(); return value

def ro_mode(path):
    if not path.exists(): return None
    db=sqlite3.connect(f"file:{path}?mode=ro",uri=True); db.execute("PRAGMA query_only=ON")
    value=db.execute("PRAGMA journal_mode").fetchone()[0].upper(); db.close(); return value

def audit_row(row, out):
    errors=[]; root=pathlib.Path(row["dir"])
    try: root.resolve().relative_to(out.resolve())
    except ValueError: errors.append("case_path_escape")
    if "control" in row:
        if row.get("result")!="REFUSED" or row.get("effects")!=0: errors.append("invalid_control_admitted")
        return errors
    p,c,m=row.get("protocol"),row.get("cut"),row.get("mode")
    if p not in ("EFFECT_FIRST","RECEIPT_FIRST","ATOMIC_LOCAL","ATOMIC_EXTERNAL") or c not in ("BEFORE","AFTER_FIRST","AFTER_SECOND","AFTER_COMMIT","NORMAL") or m not in ("DELETE","WAL"):
        errors.append("unknown_case_factor"); return errors
    effect_path=root/"effect.db" if p=="ATOMIC_EXTERNAL" else root/"local.db"
    receipt_path=root/"receipt.db" if p=="ATOMIC_EXTERNAL" else root/"local.db"
    effects=ro_count(effect_path,"effects"); receipts=ro_count(receipt_path,"receipts")
    if ro_mode(effect_path)!=m or ro_mode(receipt_path)!=m: errors.append("journal_mode_mismatch")
    if (p in ("EFFECT_FIRST","ATOMIC_EXTERNAL") and c=="AFTER_FIRST"):
        expected=(2,1,True,"NOT_FOUND")
    elif p=="RECEIPT_FIRST" and c=="AFTER_FIRST":
        expected=(0,1,False,"COMPLETED")
    else:
        expected=(1,1,c in ("BEFORE",) or (p=="ATOMIC_LOCAL" and c in ("AFTER_FIRST","AFTER_SECOND")),
                  "NOT_FOUND" if (c=="BEFORE" or (p=="ATOMIC_LOCAL" and c in ("AFTER_FIRST","AFTER_SECOND"))) else "COMPLETED")
    actual=(effects,receipts,row.get("retry"),row.get("receipt_status"))
    if actual!=expected: errors.append("outcome_mismatch")
    if effects!=row.get("effects") or receipts!=row.get("receipt_count"): errors.append("raw_db_count_mismatch")
    if row.get("child_exit") != (0 if c=="NORMAL" else 73): errors.append("child_exit_mismatch")
    snapshots=row.get("pre_recovery_files")
    if not isinstance(snapshots,list) or not snapshots: errors.append("missing_pre_recovery_snapshot")
    for item in snapshots or []:
        f=root/"pre-recovery"/item.get("name","")
        if not f.is_file(): errors.append("snapshot_missing"); continue
        b=f.read_bytes()
        if len(b)!=item.get("bytes") or hashlib.sha256(b).hexdigest()!=item.get("sha256"): errors.append("snapshot_hash_mismatch")
    return errors

def audit(path, construction=False):
    p=pathlib.Path(path); out=p.parent
    rows=json.loads(p.read_text())
    errors=[]
    wanted=32 if construction else 150
    if len(rows)!=wanted: errors.append(f"row_count:{len(rows)}")
    normal=[r for r in rows if "protocol" in r]
    controls=[r for r in rows if "control" in r]
    if construction:
        if len(normal)!=32 or controls: errors.append("construction_partition")
    elif len(normal)!=120 or len(controls)!=30: errors.append("matrix_partition")
    ids=[r.get("id") for r in rows]
    if len(set(ids))!=len(ids) or set(ids)!=set(range(wanted)): errors.append("row_id_set")
    expected_cases={(m,p,c,rep) for m in ("DELETE","WAL") for p in ("EFFECT_FIRST","RECEIPT_FIRST","ATOMIC_LOCAL","ATOMIC_EXTERNAL") for c in ("BEFORE","AFTER_FIRST","AFTER_SECOND","AFTER_COMMIT","NORMAL") for rep in range(3)}
    actual_cases={(r.get("mode"),r.get("protocol"),r.get("cut"),r.get("rep")) for r in normal}
    if construction:
        expected_cases={(m,p,c,None) for m in ("DELETE","WAL") for p in ("EFFECT_FIRST","RECEIPT_FIRST","ATOMIC_LOCAL","ATOMIC_EXTERNAL") for c in ("BEFORE","AFTER_FIRST","AFTER_SECOND","NORMAL")}
        actual_cases={(r.get("mode"),r.get("protocol"),r.get("cut"),None) for r in normal}
    if actual_cases!=expected_cases: errors.append("factor_matrix")
    if not construction:
        expected_controls={(m,c,rep) for m in ("DELETE","WAL") for c in ("ALTERED_OPERATION","WRONG_SESSION","WRONG_RESOURCE","WRONG_EPOCH","BOOL_AS_INT") for rep in range(3)}
        actual_controls={(r.get("mode"),r.get("control"),r.get("rep")) for r in controls}
        if actual_controls!=expected_controls: errors.append("control_matrix")
    for row in rows: errors.extend(f"{row.get('id')}:{e}" for e in audit_row(row,out))
    return {"schema":"wal_delete_raw_audit_v1","rows":len(rows),"case_rows":len(normal),"control_rows":len(controls),"errors":errors,
            "verdict":("PASS_CONSTRUCTION" if construction else "PASS_JOURNAL_MODE_TRANSACTION_SCOPE_SCOPED") if not errors else "FAIL_RAW_AUDIT"}

if __name__=="__main__":
    construction="--construction" in sys.argv[2:]
    result=audit(sys.argv[1],construction); print(json.dumps(result,sort_keys=True)); sys.exit(0 if not result["errors"] else 1)
