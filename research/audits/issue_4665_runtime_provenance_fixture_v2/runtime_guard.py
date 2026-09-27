"""Fail-closed comparison of observed runtime to a frozen expectation."""

from __future__ import annotations


RUNTIME_FIELDS = (
    "docker_engine",
    "daemon_platform",
    "image_id",
    "image_platform",
    "python",
)


def validate_runtime(receipt: dict, expected: dict, container_python: str) -> list[str]:
    if not isinstance(receipt, dict):
        return ["RUNTIME_RECEIPT_NOT_OBJECT"]
    errors = []
    for field in RUNTIME_FIELDS:
        observed = container_python if field == "python" else receipt.get(field)
        wanted = expected.get(field)
        if not isinstance(observed, str) or not isinstance(wanted, str):
            errors.append(f"RUNTIME_FIELD_MISSING_OR_INVALID:{field}")
        elif observed != wanted:
            errors.append(f"RUNTIME_FIELD_MISMATCH:{field}")
    return errors
