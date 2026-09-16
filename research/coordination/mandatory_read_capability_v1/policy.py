from dataclasses import dataclass

@dataclass(frozen=True)
class Receipt:
    key: str
    value: str
    revision: int

def receipt_token(receipts):
    out = {}
    for r in receipts:
        if r.key in out:
            raise ValueError('duplicate receipt')
        out[r.key] = r.revision
    return out
