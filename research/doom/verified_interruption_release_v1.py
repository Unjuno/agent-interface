"""Fail-closed evidence check for owner-originated lease interruption releases."""


def qualified_interruption_release(terminal, expected_intent_token=None):
    if (type(terminal) is not dict or terminal.get("event") != "terminal"
            or terminal.get("status") != "needs_decision"):
        return False
    interruption = terminal.get("interruption")
    if type(interruption) is not dict:
        return False
    token = interruption.get("intent_token")
    record = interruption.get("record")
    if (type(token) is not str or not token
            or (expected_intent_token is not None and token != expected_intent_token)
            or type(record) is not dict
            or record.get("event") != "owner_release"
            or record.get("intent_token") != token
            or record.get("reason") not in ("target_generation_invalidated",
                                              "target_query_invalidated")
            or record.get("verified") is not True
            or any(record.get(key) != [] for key in
                   ("keys_down", "buttons_down", "keys_unknown", "key_state_errors"))):
        return False
    reader = record.get("target_process_identity_reader")
    if type(reader) is not dict or reader.get("retired") is not True:
        return False
    attempts_by_code = record.get("key_release_attempts")
    if type(attempts_by_code) is not dict or not attempts_by_code:
        return False
    for code, receipt in attempts_by_code.items():
        if type(code) is not str or type(receipt) is not dict or receipt.get("verified") is not True:
            return False
        attempts = receipt.get("attempts")
        if type(attempts) is not list or not attempts:
            return False
        previous = None
        for index, attempt in enumerate(attempts, 1):
            if (type(attempt) is not dict or attempt.get("attempt") != index
                    or type(attempt.get("keyrelease_started_ns")) is not int
                    or type(attempt.get("sync_returned_ns")) is not int
                    or type(attempt.get("keymap_sampled_ns")) is not int
                    or not (attempt["keyrelease_started_ns"] <= attempt["sync_returned_ns"]
                            <= attempt["keymap_sampled_ns"])
                    or type(attempt.get("server_key_down_before")) is not bool
                    or type(attempt.get("server_key_down_after")) is not bool):
                return False
            if previous is not None and not (
                    previous["keymap_sampled_ns"] <= attempt["keyrelease_started_ns"]
                    and previous["server_key_down_after"] is attempt["server_key_down_before"]):
                return False
            previous = attempt
        if previous["server_key_down_after"] is not False:
            return False
    return True
