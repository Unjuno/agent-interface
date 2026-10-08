def summarize(rows):
    reasons = []
    if not isinstance(rows, list):
        return {"status": "UNKNOWN", "intervals": [], "reasons": ["rows_not_list"]}

    key_rows = [row for row in rows if isinstance(row, dict) and row.get("kind") == "key_interval"]
    empty_rows = [row for row in rows if isinstance(row, dict) and row.get("kind") == "verified_empty"]
    if (len(key_rows) + len(empty_rows) != len(rows)
            or any(not isinstance(row, dict) or row.get("kind") not in
                   ("key_interval", "verified_empty") for row in rows)):
        reasons.append("unknown_or_malformed_row")
    if not key_rows or len(empty_rows) != 1:
        reasons.append("missing_or_duplicate_required_receipt")

    first = key_rows[0] if key_rows else {}
    action_id, epoch = first.get("action_id"), first.get("epoch")
    if not isinstance(action_id, str) or not action_id or type(epoch) is not int:
        reasons.append("invalid_action_identity")

    keys = []
    intervals = []
    for row in key_rows:
        if row.get("action_id") != action_id or type(row.get("epoch")) is not int or row.get("epoch") != epoch:
            reasons.append("key_interval_identity_mismatch")
        key = row.get("key")
        if not isinstance(key, str) or not key or key in keys:
            reasons.append("duplicate_or_invalid_key")
        else:
            keys.append(key)
        if row.get("source") != "input-owner-v11":
            reasons.append("untrusted_key_source")

        names = ("press_request_ns", "press_sync_ns", "down_sample_ns",
                 "release_request_ns", "release_sync_ns", "up_sample_ns")
        if any(name not in row for name in names):
            reasons.append("missing_or_invalid_key_bracket")
            continue
        values = [row.get(name) for name in names]
        if any(type(value) is not int or value < 0 for value in values):
            reasons.append("invalid_timestamp_order_or_type")
            continue
        p_req, p_sync, d_sample, r_req, r_sync, u_sample = values
        if not (p_req <= p_sync <= d_sample < r_req <= r_sync <= u_sample):
            reasons.append("invalid_timestamp_order_or_type")
            continue
        intervals.append({"action_id": action_id, "epoch": epoch, "key": key,
                          "lower_ns": r_req - p_sync,
                          "upper_ns": r_sync - p_req})

    if len(empty_rows) == 1:
        empty = empty_rows[0]
        stamp = empty.get("timestamp_ns")
        if (empty.get("action_id") != action_id or type(empty.get("epoch")) is not int
                or empty.get("epoch") != epoch):
            reasons.append("empty_receipt_identity_mismatch")
        if empty.get("source") != "xquerykeymap" or empty.get("keys_down") != []:
            reasons.append("empty_receipt_not_verified")
        if type(stamp) is not int or stamp < 0 or any(
                row.get("up_sample_ns", stamp + 1) > stamp for row in key_rows):
            reasons.append("empty_receipt_before_key_release")

    reasons = sorted(set(reasons))
    if reasons:
        return {"status": "UNKNOWN", "intervals": [], "reasons": reasons}
    return {"status": "BOUNDED", "intervals": sorted(intervals, key=lambda row: row["key"]),
            "reasons": []}
