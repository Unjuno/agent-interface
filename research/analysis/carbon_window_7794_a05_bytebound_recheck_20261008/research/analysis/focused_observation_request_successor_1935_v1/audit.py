import json
from itertools import product

def expected():
    rows = []
    for epoch, ident, flip in product((1, 2), ("A", "B"), (0, 1)):
        for req_epoch, req_ident, region, reason in product(
            (1, 2), ("A", "B"),
            ((1, 1, 2, 2), (0, 0, 3, 3), (-1, 0, 2, 2), (1, 1, 1, 2)),
            ("uncertain", "inferred"),
        ):
            x0, y0, x1, y1 = region
            ok = reason == "uncertain" and epoch == req_epoch and ident == req_ident and 0 <= x0 < x1 <= 3 and 0 <= y0 < y1 <= 3
            rows.append(ok)
    return rows

rows = expected()
assert len(rows) == 256
assert sum(rows) == 16
assert len(rows) - sum(rows) == 240
print(json.dumps({"independent_rows": len(rows), "independent_valid": sum(rows), "independent_rejected": 240, "audit": "PASS"}))
