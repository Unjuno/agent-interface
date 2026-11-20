import hashlib, hmac, json, secrets, sys
from pathlib import Path

N_PERIODS = 4
SLOTS = 2
LEAVES = N_PERIODS * SLOTS

def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
def sha(b): return hashlib.sha256(b).digest()
def hx(b): return b.hex()
def child(seed, side): return hmac.new(seed, b"fss-tree-v1" + bytes([side]), hashlib.sha256).digest()
def leaf_seed(root, index):
    node = root
    for shift in (2, 1, 0): node = child(node, (index >> shift) & 1)
    return node

def ots_secret(seed, pos, bit):
    return hmac.new(seed, b"lamport-v1" + pos.to_bytes(2, "big") + bytes([bit]), hashlib.sha256).digest()
def ots_public(seed):
    return [[hx(sha(ots_secret(seed, p, b))) for b in (0, 1)] for p in range(256)]
def ots_sign(seed, message):
    d = sha(message)
    return [hx(ots_secret(seed, p, (d[p // 8] >> (7 - p % 8)) & 1)) for p in range(256)]
def ots_verify(pub, message, sig):
    if len(sig) != 256 or len(pub) != 256: return False
    d = sha(message)
    try:
        for p, value in enumerate(sig):
            b = (d[p // 8] >> (7 - p % 8)) & 1
            if hx(sha(bytes.fromhex(value))) != pub[p][b]: return False
    except (ValueError, TypeError, IndexError): return False
    return True

def leaf_hash(pub): return sha(b"LEAF1" + canon(pub))
def merkle_levels(pubs):
    levels = [[leaf_hash(p) for p in pubs]]
    while len(levels[-1]) > 1:
        row = levels[-1]
        levels.append([sha(b"NODE1" + row[i] + row[i + 1]) for i in range(0, len(row), 2)])
    return levels
def proof(levels, index):
    out, i = [], index
    for level in levels[:-1]:
        sibling = i ^ 1
        out.append({"side": "L" if sibling < i else "R", "hash": hx(level[sibling])})
        i //= 2
    return out

def msg_for(period, slot, body):
    return canon({"period": period, "slot": slot, "body_sha256": hx(sha(canon(body)))})
def head_for(previous, body): return hx(sha(b"HEAD1" + bytes.fromhex(previous) + sha(canon(body))))

def frontier_consume(frontier):
    start, size, seed = frontier.pop(0)
    siblings = []
    while size > 1:
        half = size // 2
        left, right = child(seed, 0), child(seed, 1)
        siblings.append((start + half, half, right))
        seed, size = left, half
    return seed, sorted(siblings + frontier, key=lambda row: row[0])

def build():
    static_seeds = [secrets.token_bytes(32) for _ in range(LEAVES)]
    fss_root_seed = secrets.token_bytes(32)
    fss_seeds = [leaf_seed(fss_root_seed, i) for i in range(LEAVES)]
    static_pubs = [ots_public(s) for s in static_seeds]
    fss_pubs = [ots_public(s) for s in fss_seeds]
    fss_levels = merkle_levels(fss_pubs)
    static_registry_hash = hx(sha(canon(static_pubs)))
    fss_root = hx(fss_levels[-1][0])

    records, heads = [], []
    prev = "00" * 32
    for period in range(1, N_PERIODS + 1):
        claim = "saved" if period == 2 else f"event-{period}"
        body = {"event_id": f"receipt-{period}", "period": period, "claim": claim, "previous_head": prev}
        idx = (period - 1) * SLOTS
        message = msg_for(period, 0, body)
        record = {
            "period": period, "slot": 0, "body": body,
            "sig_static": ots_sign(static_seeds[idx], message),
            "sig_fss": ots_sign(fss_seeds[idx], message),
            "fss_proof": proof(fss_levels, idx),
        }
        records.append(record)
        prev = head_for(prev, body)
        heads.append(prev)
        # Model forward-frontier retirement: consume each used slot in order.
        # The retained tree state after leaf 6 is exactly leaf 7.
    frontier = [(0, LEAVES, fss_root_seed)]
    for i in range(LEAVES - 1):
        secret, frontier = frontier_consume(frontier)
        if hx(secret) != hx(fss_seeds[i]): raise AssertionError("frontier/leaf derivation mismatch")
    if len(frontier) != 1 or frontier[0][0] != LEAVES - 1 or frontier[0][1] != 1:
        raise AssertionError("current frontier is not the final unspent leaf")
    if hx(frontier[0][2]) != hx(fss_seeds[-1]): raise AssertionError("frontier current secret mismatch")

    witness_seeds = [secrets.token_bytes(32) for _ in range(N_PERIODS)]
    witness_pubs = [ots_public(s) for s in witness_seeds]
    checkpoints = []
    for period, (head, seed) in enumerate(zip(heads, witness_seeds), 1):
        payload = canon({"period": period, "head": head})
        checkpoints.append({"period": period, "head": head, "pub": witness_pubs[period - 1], "sig": ots_sign(seed, payload)})

    fixture = {
        "schema": "UNJUNO-7825-FSS-A01-FIXTURE-v1",
        "periods": N_PERIODS, "slots_per_period": SLOTS,
        "static_registry_hash": static_registry_hash,
        "static_pubkeys": static_pubs,
        "fss_root": fss_root,
        "fss_pubkeys": fss_pubs,
        "records": records,
        "checkpoints": checkpoints,
        "checkpoint_registry_hash": hx(sha(canon(witness_pubs))),
        "heads": heads,
        "test_compromise": {
            "period": N_PERIODS, "slot": 1,
            "static_leaf_seed": hx(static_seeds[-1]),
            "fss_frontier_leaf_seed": hx(frontier[0][2]),
            "fss_next_leaf_index": LEAVES - 1,
            "notice": "Synthetic attack input intentionally public; never a production key."
        }
    }
    return fixture

if __name__ == "__main__":
    fixture = build()
    target = Path(sys.argv[1])
    target.write_bytes(canon(fixture) + b"\n")
    print(json.dumps({"status":"CONSTRUCTION_FIXTURE_READY","path":str(target),"periods":N_PERIODS,"records":len(fixture["records"]),"fss_root":fixture["fss_root"],"test_compromise_public":True},sort_keys=True,separators=(",",":")))
