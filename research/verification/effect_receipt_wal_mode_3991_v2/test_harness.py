#!/usr/bin/env python3
"""Construction-only deterministic guard/schema checks; no formal allocation."""
import pathlib, sys, tempfile
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import runner

def main():
    expected={"op_id":"op","payload":"payload","session":"session","resource":"resource","epoch":1}
    bad=[]
    for key,value in (("payload","x"),("session","x"),("resource","x"),("epoch",2),("epoch",True)):
        c=dict(expected); c[key]=value
        if runner.guard_identity(expected,c): bad.append((key,value))
    if bad: raise SystemExit(f"invalid identity admitted: {bad}")
    if not runner.guard_identity(expected,dict(expected)): raise SystemExit("valid identity refused")
    with tempfile.TemporaryDirectory() as td:
        path=pathlib.Path(td)/"all-tables.db"
        runner.init_db(path,"DELETE",("effects","receipts"))
        import sqlite3
        db=sqlite3.connect(path)
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}; db.close()
        if not {"effects","receipts"}.issubset(tables): raise SystemExit(f"schema incomplete: {tables}")
    print("PASS_CONSTRUCTION_UNIT guard=6/6 tables=2/2")
if __name__=="__main__": main()
