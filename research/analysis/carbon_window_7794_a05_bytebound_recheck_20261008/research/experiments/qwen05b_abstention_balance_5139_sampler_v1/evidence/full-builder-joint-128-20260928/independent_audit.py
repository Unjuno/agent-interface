from collections import Counter, defaultdict
import hashlib

CLASSES=("set","save","toggle","yield:forbidden","yield:ambiguous","yield:stale_scope","yield:missing_evidence","no_action:already_satisfied")
COUNTS={"imbalanced":{"set":16,"save":4,"toggle":4,"yield:forbidden":1,"yield:ambiguous":1,"yield:stale_scope":1,"yield:missing_evidence":1,"no_action:already_satisfied":4},"balanced":{c:4 for c in CLASSES}}

def _rank(seed, cls, case):
    payload=b"support-row-rank-v1\n"+str(seed).encode("ascii")+b"\n"+cls.encode("utf-8")+b"\n"+case.encode("utf-8")
    return hashlib.sha256(payload).digest()

def _cell(row):
    index=int(row["case_id"].split("-")[1]); q,k=divmod(index,8)
    return q%4,(q+k)%4

def audit_document(document):
    errors=[]; seed=document.get("support_seed"); pool=document.get("support_pool"); supports=document.get("supports")
    if isinstance(seed,bool) or not isinstance(seed,int) or seed<=0: return ["bad_support_seed"]
    if not isinstance(pool,list) or not isinstance(supports,dict): return ["bad_dataset_shape"]
    grouped=defaultdict(list); seen=set()
    for row in pool:
        if not isinstance(row,dict): errors.append("bad_pool_row"); continue
        cid=row.get("case_id"); cls=row.get("class")
        if not isinstance(cid,str) or not cid or cid in seen: errors.append("bad_or_duplicate_pool_id"); continue
        seen.add(cid)
        if cls not in CLASSES: errors.append("unknown_pool_class"); continue
        grouped[cls].append(row)
    cells=defaultdict(list)
    for row in grouped["set"]: cells[_cell(row)].append(row)
    chosen_cells=[(t,(t+seed%4)%4) for t in range(4)]
    expected={"imbalanced":{},"balanced":{}}
    if len(cells)!=16 or any(len(v)!=4 for v in cells.values()): errors.append("pool_cell_shape")
    else:
        for cell in chosen_cells:
            expected["imbalanced"]["set"] = expected["imbalanced"].get("set",[])+sorted(cells[cell],key=lambda r:r["case_id"].encode("utf-8"))
            expected["balanced"]["set"] = expected["balanced"].get("set",[])+[min(cells[cell],key=lambda r:(_rank(seed,"set",r["case_id"]),r["case_id"].encode("utf-8")))]
    for cls in CLASSES:
        if cls=="set": continue
        ranked=sorted(grouped[cls],key=lambda r:(_rank(seed,cls,r["case_id"]),r["case_id"].encode("utf-8")))
        for arm in expected: expected[arm][cls]=ranked[:COUNTS[arm][cls]]
    for arm in COUNTS:
        actual=supports.get(arm)
        if not isinstance(actual,list): errors.append("missing_arm:"+arm); continue
        expected_rows=[row for cls in CLASSES for row in expected[arm].get(cls,[])]
        if [r.get("case_id") for r in actual]!=[r["case_id"] for r in expected_rows]: errors.append("id_order:"+arm)
        if actual!=expected_rows: errors.append("row_content:"+arm)
        counts=Counter(r.get("class") for r in actual if isinstance(r,dict))
        if len(actual)!=sum(COUNTS[arm].values()) or any(counts[c]!=COUNTS[arm][c] for c in CLASSES): errors.append("quotas:"+arm)
        set_rows=[r for r in actual if r.get("class")=="set"]
        joint={_cell(r) for r in set_rows}; templates=Counter(t for t,f in joint)
        tcounts=Counter(_cell(r)[0] for r in set_rows); fcounts=Counter(_cell(r)[1] for r in set_rows)
        per=1 if arm=="balanced" else 4
        if joint!=set(chosen_cells) or sorted(tcounts.values())!=[per]*4 or sorted(fcounts.values())!=[per]*4: errors.append("joint_marginals:"+arm)
    b={r["case_id"] for r in supports.get("balanced",[]) if r.get("class")=="set"}; i={r["case_id"] for r in supports.get("imbalanced",[]) if r.get("class")=="set"}
    if not b<=i: errors.append("set_not_nested")
    return errors

