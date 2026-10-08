"""Content-bound barrier confirmation policy for Issue #449.

The classifier intentionally receives only readback evidence, never the preceding
successful update response. Exact UTF-8 content equality is required before the
coordination generation may advance.
"""


def classify(readback_text, expected_text, unavailable=False):
    if unavailable:
        return {"classification": "BARRIER_UNKNOWN", "advance_coordination": False, "receiver_recovery_put": False}
    if readback_text == expected_text:
        return {"classification": "BARRIER_CONFIRMED", "advance_coordination": True, "receiver_recovery_put": False}
    return {"classification": "BARRIER_CONFLICT", "advance_coordination": False, "receiver_recovery_put": False}
