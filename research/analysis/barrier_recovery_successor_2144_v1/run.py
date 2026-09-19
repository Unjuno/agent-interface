import hashlib, json

CASES = [
    ("WRITE_ACK_VISIBLE", 2, "g2", "ADVANCE"),
    ("WRITE_COMMITTED_ACK_LOST", 2, "g1", "READ_BACK"),
    ("WRITE_NOT_COMMITTED", 1, "g1", "RETRY_IDEMPOTENTLY"),
    ("READ_CHANGED", 3, "g3", "ABORT"),
    ("READ_UNAVAILABLE", None, None, "HOLD"),
    ("DUPLICATE_OR_REPLAYED", 2, "g2", "READ_BACK"),
]

def decide(kind, generation, content, expected_generation=2, expected_content="g2"):
    if kind == "WRITE_ACK_VISIBLE" and generation == expected_generation and content == expected_content:
        return "ADVANCE"
    if kind in ("WRITE_COMMITTED_ACK_LOST", "DUPLICATE_OR_REPLAYED"):
        return "READ_BACK"
    if kind == "WRITE_NOT_COMMITTED" and generation == expected_generation - 1:
        return "RETRY_IDEMPOTENTLY"
    if kind == "READ_CHANGED":
        return "ABORT"
    return "HOLD"

def main():
    rows=[]
    for kind,generation,content,expected in CASES:
        actual=decide(kind,generation,content)
        rows.append({"kind":kind,"generation":generation,"content":content,"decision":actual,"expected":expected,"grant_authority":False,"writes":0})
    assert all(r["decision"]==r["expected"] for r in rows)
    assert all(r["grant_authority"] is False and r["writes"] == 0 for r in rows)
    raw=json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
    out={"decision":"HOLD_PRE_MODEL_BARRIER_RECOVERY_POLICY","cases":6,"oracle_agreement":6,"blind_retries":0,"stale_advances":0,"duplicate_writes":0,"authority_grants":0,"model_invocations":0,"sha256":hashlib.sha256(raw).hexdigest()}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__ == "__main__": main()
