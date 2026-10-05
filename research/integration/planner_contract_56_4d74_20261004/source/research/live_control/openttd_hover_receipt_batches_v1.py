"""Compose bounded hover programs into one meaning-free evidence set."""
from openttd_hover_receipt_v1 import verify


def verify_batches(batches, runtime_dir, maximum_points=7):
    if not isinstance(batches, list) or not batches:
        raise ValueError("one or more hover batches required")
    binding = None
    receipts = []
    seen = set()
    for batch in batches:
        if not isinstance(batch, dict) or set(batch) != {"records", "steps", "points"}:
            raise ValueError("exact batch fields required")
        if not 1 <= len(batch["points"]) <= 3:
            raise ValueError("each batch must contain one to three points")
        ready = verify(batch["records"], batch["steps"], batch["points"], runtime_dir)
        if binding is None:
            binding = ready["binding"]
        elif ready["binding"] != binding:
            raise ValueError("pointer binding changed across hover batches")
        for receipt in ready["receipts"]:
            point = tuple(receipt["point"])
            if point in seen:
                raise ValueError("duplicate point across hover batches")
            seen.add(point)
            copied = dict(receipt)
            copied["receipt_index"] = len(receipts) + 1
            receipts.append(copied)
    if len(receipts) > maximum_points:
        raise ValueError("too many hover receipts")
    return {"status": "READY", "binding": binding, "receipts": receipts,
            "batches": len(batches),
            "authority": "composed observation evidence only; grants no input authority"}
