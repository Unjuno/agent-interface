"""Frozen admission policy for Issue #433.

Pure fixture logic only.  Receiver BLOCKED state is checked before generation
admission; generation admission is checked before request replay/idempotency.
"""


def classify(receiver, request):
    if receiver["mode"] != "ACTIVE":
        return "BARRIER_BLOCKED"
    if request["generation"] != receiver["accepted_generation"]:
        return "FENCED_STALE"
    prior = receiver["receipts"].get(request["request_id"])
    if prior is not None:
        same = (
            prior["generation"] == request["generation"]
            and prior["fingerprint"] == request["fingerprint"]
        )
        return "REPLAY_APPLIED" if same else "CONFLICT"
    return "APPLY"
