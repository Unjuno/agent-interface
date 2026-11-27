"""Conservative token-ownership precheck; never certifies input release."""

def token_precheck(events):
    if not isinstance(events, list) or any(not isinstance(row, dict) for row in events):
        return {"status": "HOLD_AMBIGUOUS_TOKEN", "formal_pass": False}
    cancellations = [row.get("id") for row in events if row.get("event") == "cancel_requested"]
    if (not cancellations or any(type(ident) is not str or not ident for ident in cancellations)
            or len(cancellations) != len(set(cancellations))):
        return {"status": "HOLD_AMBIGUOUS_TOKEN", "formal_pass": False}
    tokens_by_id = {ident: set() for ident in cancellations}
    for row in events:
        if row.get("event") != "input_admission":
            continue
        ident, token = row.get("id"), row.get("intent_token")
        if (type(ident) is not str or ident not in tokens_by_id
                or type(token) is not str or not token):
            return {"status": "HOLD_AMBIGUOUS_TOKEN", "formal_pass": False}
        tokens_by_id[ident].add(token)
    owners = {}
    for ident, tokens in tokens_by_id.items():
        if len(tokens) > 1:
            return {"status": "HOLD_AMBIGUOUS_TOKEN", "formal_pass": False}
        for token in tokens:
            if token in owners and owners[token] != ident:
                return {"status": "HOLD_AMBIGUOUS_TOKEN", "formal_pass": False}
            owners[token] = ident
    return {"status": "READY_FOR_FURTHER_CHECKS", "formal_pass": False}
