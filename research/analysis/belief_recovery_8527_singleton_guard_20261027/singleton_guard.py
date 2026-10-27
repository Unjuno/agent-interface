"""Construction-only guard for A02 singleton-control coverage.

The frozen A02 auditor is not modified. A future version must explicitly
compose this guard with an independently validated policy audit.
"""


def _identity(value):
    if (type(value) is not list or len(value) != 1
            or type(value[0]) is not str or not value[0]):
        raise ValueError("singleton belief must contain one nonempty state")
    return value[0]


def validate_singleton_controls(fixture, raw):
    if type(fixture) is not dict or type(raw) is not dict:
        raise ValueError("fixture and raw output must be objects")
    cases = fixture.get("cases")
    if type(cases) is not list:
        raise ValueError("fixture cases must be a list")
    matching = [case for case in cases if type(case) is dict
                and case.get("id") == "aliased-opposite-actions"]
    if len(matching) != 1:
        raise ValueError("exactly one singleton-control case is required")
    declared = matching[0].get("singleton_controls")
    rows = raw.get("singleton_controls")
    if type(declared) is not list or not declared or type(rows) is not list:
        raise ValueError("declared controls and result rows must be lists")
    expected = [_identity(belief) for belief in declared]
    if len(expected) != len(set(expected)):
        raise ValueError("duplicate singleton-control declaration")
    observed = []
    for row in rows:
        if type(row) is not dict:
            raise ValueError("singleton-control row must be an object")
        observed.append(_identity(row.get("belief")))
    if len(observed) != len(expected) or set(observed) != set(expected):
        raise ValueError("singleton-control identity coverage mismatch")


def audit_with_guard(fixture, raw, frozen_digest, truth, legacy_audit):
    validate_singleton_controls(fixture, raw)
    return legacy_audit(fixture, raw, frozen_digest, truth)
