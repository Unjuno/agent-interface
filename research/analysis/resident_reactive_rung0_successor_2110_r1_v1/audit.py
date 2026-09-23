import json

def oracle(trace): return sum(1 for i,s in enumerate(trace) if s and (i==0 or not trace[i-1]))
def main():
    with open("RESULT.json",encoding="utf-8") as f: rows=json.load(f)["rows_detail"]
    assert len(rows)==64
    for row in rows:
        effects=[e for e in row["resident"] if e[0]=="effect"]
        assert len(effects)==oracle(row["trace"])
        assert row["stale_rejections"]==1 and row["resident"][-1]==["release",4,1] and row["valid"] is True
    print("independent_audit=PASS rows=64 stale_rejections=64 release=PASS")
if __name__=="__main__": main()
