"""Frozen synthetic application-effect scorer v1."""


def score(record):
    if record.get("status") != "COMPLETE":
        return "UNKNOWN"
    if (record.get("target") == "expected" and record.get("durable") is True
            and record.get("collateral") is False):
        return "PASS"
    return "FAIL"
