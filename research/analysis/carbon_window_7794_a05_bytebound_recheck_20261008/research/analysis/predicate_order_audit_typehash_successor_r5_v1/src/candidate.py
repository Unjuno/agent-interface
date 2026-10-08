"""Exact JSON type-shape gate layered over the retained raw auditor."""
from __future__ import annotations


class TypeShapeReject(ValueError):
    pass


def require_same_json_types(value, reference, path="$", depth=0):
    if depth > 64:
        raise TypeShapeReject("depth:" + path)
    if type(value) is not type(reference):
        raise TypeShapeReject("type:" + path)
    if type(reference) is dict:
        if set(value) != set(reference):
            raise TypeShapeReject("keys:" + path)
        for key in reference:
            require_same_json_types(value[key], reference[key], path + "." + key,
                                    depth + 1)
    elif type(reference) is list:
        if len(value) != len(reference):
            raise TypeShapeReject("length:" + path)
        for index, (item, expected) in enumerate(zip(value, reference)):
            require_same_json_types(item, expected, f"{path}[{index}]", depth + 1)


def audit_document(candidate, reference, raw_auditor):
    require_same_json_types(candidate, reference)
    return raw_auditor.audit_document(candidate)
