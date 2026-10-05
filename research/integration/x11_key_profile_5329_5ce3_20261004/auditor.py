"""Independent saved source/projection/wire oracle; never imports codec."""
import argparse,hashlib,itertools,json
from pathlib import Path
POLICIES=("RAW_CHECKPOINT","RECEIPT_TRUST","KEY_SUBSET","CONSERVATIVE_PROFILE")
def need(v,m):
    if not v:raise ValueError(m)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def truth(record):
    o=record["observation"];bits=int.from_bytes(bytes.fromhex(o["keymap"]),"little");c=record["meta"]["keycodes"]
    return {"owned_up":not bool((bits>>c["F8"])&1),"bystander_held":bool((bits>>c["F9"])&1)if record["meta"]["bystander_required"]else None,"all_keys_neutral_buttons123":bits==0 and o["buttons"]==0,"scoped_verified":o["scoped_verified"]}
def validate_packet(row,record):
    need(row["case_id"]==record["case_id"]and row["family"]==record["family"],"membership")
    need(row["packet"]["meta"]==record["meta"],"lossless selected metadata")
    w=canonical(row["packet"]);need(type(row["bytes"])is int and row["bytes"]==len(w)and bytes.fromhex(row["wire_hex"])==w,"full canonical wire join")
    o=record["observation"];t=truth(record);p=row["policy"]
    b=int.from_bytes(bytes.fromhex(o["keymap"]),"little");c=record["meta"]["keycodes"]
    k=((b>>c["F8"])&1)+2*((b>>c["F9"])&1)
    if p=="RAW_CHECKPOINT":payload=o;decision=t
    elif p=="RECEIPT_TRUST":
        payload={"v":o["scoped_verified"]};decision={"owned_up":o["scoped_verified"],"bystander_held":None,"all_keys_neutral_buttons123":o["scoped_verified"],"scoped_verified":o["scoped_verified"]}
    elif p in("KEY_SUBSET","CONSERVATIVE_PROFILE"):
        payload={"k":k,"b":o["buttons"],"v":o["scoped_verified"]};decision=dict(t)
        if p=="KEY_SUBSET":decision["all_keys_neutral_buttons123"]=None
        else:payload["o"]=bool(b & ~((1<<c["F8"])|(1<<c["F9"])))
    else:raise ValueError("unknown policy")
    need(row["packet"]["payload"]==payload and row["decision"]==decision,"source encoding/declared decoder")
    return True
def reconstruct_input(raw):
    records=[]
    for i,line in enumerate(raw.splitlines()):
        r=json.loads(line);samples=[s for s in r["samples"]if s["tag"]=="checkpoint"]
        need(len(samples)==1 and r["error"]is None,"native valid checkpoint");s=samples[0];c=r["capability"]
        m={"id":"N%02d"%i,"source_sha256":hashlib.sha256(raw).hexdigest(),"row_sha256":hashlib.sha256(line).hexdigest(),"owner":[c["owner_pid"],c["owner_start_ticks"]],"nonce":c["owner_nonce"],"display":[c["display_pid"],c["display_start_ticks"],c["window_id"]],"keycodes":r["keycodes"],"interval":[s["query_started_ns"],s["at_ns"]],"bystander_required":r["context"]=="crash_bystander"}
        records.append({"case_id":m["id"],"family":"native","meta":m,"observation":{"keymap":s["keymap"],"buttons":s["buttons"],"scoped_verified":r["supervisor"]["result"]["receipt"]["verified"]}})
    for i in range(32):
        vector=(int(bool(i&1))<<74)|(int(bool(i&2))<<75)|(int(bool(i&4))<<76)
        m={"id":"SYNTHETIC_IDENTITY","source_sha256":"finite-state-family-v1","owner":[1,1],"nonce":"synthetic","display":[2,2,3],"keycodes":{"F8":74,"F9":75},"interval":[10,11],"bystander_required":True}
        records.append({"case_id":"S%02d"%i,"family":"synthetic","meta":m,"observation":{"keymap":vector.to_bytes(32,"little").hex(),"buttons":256 if i&8 else 0,"scoped_verified":bool(i&16)}})
    return records
def analyze(records,rows,plan):
    need(len(records)==50 and len(rows)==200,"50 records/four policy matrix")
    known={r["case_id"]:r for r in records}
    need(len(known)==50 and len({(r["case_id"],r["policy"])for r in rows})==200,"unique packet matrix")
    totals={f:{p:{"rows":0,"bytes":0,"mismatched_predicates":0,"unknown_predicates":0,"false_positive_predicates":0,"predicate_projection_collision_pairs":0}for p in POLICIES}for f in("native","synthetic")}
    grouped={}
    for r in rows:
        rec=known[r["case_id"]];validate_packet(r,rec);t=truth(rec);d=r["decision"];v=totals[r["family"]][r["policy"]]
        v["rows"]+=1;v["bytes"]+=r["bytes"]
        for key in plan["predicate_names"]:
            v["mismatched_predicates"]+=int(d[key]!=t[key])
            v["unknown_predicates"]+=int(d[key]is None and t[key]is not None)
            v["false_positive_predicates"]+=int(d[key]is True and t[key]is False)
        key=(r["family"],r["policy"],canonical([rec["meta"]["keycodes"],rec["meta"]["bystander_required"],r["packet"]["payload"]]))
        grouped.setdefault(key,[]).append(canonical(t))
    for (family,policy,_),values in grouped.items():
        totals[family][policy]["predicate_projection_collision_pairs"]+=sum(a!=b for a,b in itertools.combinations(values,2))
    native=totals["native"];gain=1-native["CONSERVATIVE_PROFILE"]["bytes"]/native["RAW_CHECKPOINT"]["bytes"]
    preservation=all(totals[f]["CONSERVATIVE_PROFILE"]["mismatched_predicates"]==0 for f in totals)
    status="FAIL_CONSERVATIVE_PREDICATE"if not preservation else "PASS_NATIVE_RECORD_PROFILE_SCOPED"if gain>=plan["minimum_complete_packet_reduction"]else"FAIL_PACKET_BYTE_GATE"
    return {"status":status,"predicate_preservation_scoped":preservation,"native_complete_packet_reduction":gain,"totals":totals,"native_rows":18,"synthetic_states":32,"packets":200,"native_inputs":0,"original_native_regraded":False,"token_latency_product_benefit_established":False,"collision_scope":"semantic payload/keycode/bystander projection only, NOT full-provenance wire aliases"}
def main():
    p=argparse.ArgumentParser();p.add_argument("input");p.add_argument("packets");p.add_argument("source_raw");p.add_argument("out");a=p.parse_args()
    try:
        plan=json.loads((Path(__file__).parent/"PLAN.json").read_text());raw=Path(a.source_raw).read_bytes()
        need(hashlib.sha256(raw).hexdigest()==plan["raw_sha256"],"immutable original native raw hash")
        records=reconstruct_input(raw);inp=json.loads(Path(a.input).read_text())
        need(inp["records"]==records and inp["raw_sha256"]==plan["raw_sha256"],"candidate input/native source reconstruction")
        rows=[json.loads(s)for s in Path(a.packets).read_text().splitlines()]
        result=analyze(records,rows,plan);result["input_sha256"]=hashlib.sha256(Path(a.input).read_bytes()).hexdigest();result["packets_sha256"]=hashlib.sha256(Path(a.packets).read_bytes()).hexdigest();result["source_raw_sha256"]=hashlib.sha256(raw).hexdigest();code=0
    except Exception as e:result={"status":"STOP_INVALID_EVIDENCE","error":repr(e)};code=1
    with Path(a.out).open("x")as f:json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps(result));raise SystemExit(code)
if __name__=="__main__":main()
