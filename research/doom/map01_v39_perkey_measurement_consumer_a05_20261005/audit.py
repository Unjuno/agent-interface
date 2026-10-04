"""Independent raw-row identity reconstruction with exact type checks."""


def independently_reconstruct(rows):
    if type(rows) is not list or len(rows) != 2:
        raise ValueError("expected one pair")
    result = []
    for event in rows:
        if type(event) is not dict:
            raise ValueError("row must be an object")
        program = event.get("id")
        step = event.get("step")
        owner = event.get("owner_id")
        intent = event.get("intent_token")
        key = event.get("key")
        if type(program) is not str or program == "":
            raise ValueError("invalid program id type/value")
        if type(step) is not int or step < 0:
            raise ValueError("invalid step type/value")
        if any(type(x) is not str or x == "" for x in (owner, intent, key)):
            raise ValueError("invalid owner/intent/key type/value")
        result.append((program, step, owner, intent, key))
    if result[0] != result[1]:
        raise ValueError("pair identity mismatch")
    return result[0]
