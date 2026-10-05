"""Independent declarative expected outcomes for Issue #7865 T0 A01."""

from copy import deepcopy


def _s(identity, generation, title, body, title_rev, body_rev):
    return {"identity": identity, "generation": generation,
            "fields": {"title": title, "body": body},
            "field_revisions": {"title": title_rev, "body": body_rev}}


BASE = _s("doc-A", 0, "A", "x", 0, 0)
AGENT = _s("doc-A", 1, "B", "x", 1, 0)
EXPECT = {
    "none": {
        "BLIND_INVERSE": ("COMPENSATED_NEW_EFFECT", BASE, True),
        "WHOLE_OBJECT_VERSION_GUARD": ("COMPENSATED_NEW_EFFECT", BASE, True),
        "FIELD_SCOPED_COMPARE_AND_COMPENSATE":
            ("COMPENSATED_NEW_EFFECT", _s("doc-A", 2, "A", "x", 2, 0), True),
        "NO_AUTO_COMPENSATION": ("CONFLICT_OR_HOLD", AGENT, False)},
    "disjoint": {
        "BLIND_INVERSE": ("COMPENSATED_NEW_EFFECT", BASE, True),
        "WHOLE_OBJECT_VERSION_GUARD":
            ("CONFLICT_OR_HOLD", _s("doc-A", 2, "B", "y", 1, 1), False),
        "FIELD_SCOPED_COMPARE_AND_COMPENSATE":
            ("COMPENSATED_NEW_EFFECT", _s("doc-A", 3, "A", "y", 2, 1), True),
        "NO_AUTO_COMPENSATION":
            ("CONFLICT_OR_HOLD", _s("doc-A", 2, "B", "y", 1, 1), False)},
    "same_field": {
        "BLIND_INVERSE": ("COMPENSATED_NEW_EFFECT", BASE, True),
        "WHOLE_OBJECT_VERSION_GUARD":
            ("CONFLICT_OR_HOLD", _s("doc-A", 2, "C", "x", 2, 0), False),
        "FIELD_SCOPED_COMPARE_AND_COMPENSATE":
            ("CONFLICT_OR_HOLD", _s("doc-A", 2, "C", "x", 2, 0), False),
        "NO_AUTO_COMPENSATION":
            ("CONFLICT_OR_HOLD", _s("doc-A", 2, "C", "x", 2, 0), False)},
    "aba": {
        "BLIND_INVERSE": ("COMPENSATED_NEW_EFFECT", BASE, True),
        "WHOLE_OBJECT_VERSION_GUARD":
            ("CONFLICT_OR_HOLD", _s("doc-A", 3, "B", "x", 3, 0), False),
        "FIELD_SCOPED_COMPARE_AND_COMPENSATE":
            ("CONFLICT_OR_HOLD", _s("doc-A", 3, "B", "x", 3, 0), False),
        "NO_AUTO_COMPENSATION":
            ("CONFLICT_OR_HOLD", _s("doc-A", 3, "B", "x", 3, 0), False)},
    "replacement": {
        "BLIND_INVERSE": ("COMPENSATED_NEW_EFFECT", BASE, True),
        "WHOLE_OBJECT_VERSION_GUARD":
            ("CONFLICT_OR_HOLD", _s("doc-B", 0, "B", "x", 0, 0), False),
        "FIELD_SCOPED_COMPARE_AND_COMPENSATE":
            ("CONFLICT_OR_HOLD", _s("doc-B", 0, "B", "x", 0, 0), False),
        "NO_AUTO_COMPENSATION":
            ("CONFLICT_OR_HOLD", _s("doc-B", 0, "B", "x", 0, 0), False)},
    "unknown": {
        "BLIND_INVERSE": ("COMPENSATED_NEW_EFFECT", BASE, True),
        "WHOLE_OBJECT_VERSION_GUARD":
            ("CONFLICT_OR_HOLD", AGENT, False),
        "FIELD_SCOPED_COMPARE_AND_COMPENSATE":
            ("CONFLICT_OR_HOLD", AGENT, False),
        "NO_AUTO_COMPENSATION":
            ("CONFLICT_OR_HOLD", AGENT, False)},
    "out_of_order": {
        "BLIND_INVERSE": ("COMPENSATED_NEW_EFFECT", BASE, True),
        "WHOLE_OBJECT_VERSION_GUARD":
            ("CONFLICT_OR_HOLD", _s("doc-A", 3, "B", "z", 1, 2), False),
        "FIELD_SCOPED_COMPARE_AND_COMPENSATE":
            ("CONFLICT_OR_HOLD", _s("doc-A", 3, "B", "z", 1, 2), False),
        "NO_AUTO_COMPENSATION":
            ("CONFLICT_OR_HOLD", _s("doc-A", 3, "B", "z", 1, 2), False)},
}


def independently_expected(name, policy):
    disposition, state, wrote = EXPECT[name][policy]
    return {"disposition": disposition, "state": deepcopy(state),
            "wrote": wrote, "literal_rollback": False}


def assert_matches(results):
    for name, row in EXPECT.items():
        for policy in row:
            actual = results[name][policy]
            expected = independently_expected(name, policy)
            if actual != expected:
                raise AssertionError((name, policy, expected, actual))
    return sum(len(row) for row in EXPECT.values())
