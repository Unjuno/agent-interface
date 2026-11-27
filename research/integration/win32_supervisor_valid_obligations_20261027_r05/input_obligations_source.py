"""Conservative release obligations derived from a standard input program."""
from __future__ import annotations


def _utf16_units(value: str) -> tuple[int, ...]:
    encoded = value.encode("utf-16-le", errors="strict")
    return tuple(encoded[index] | encoded[index + 1] << 8
                 for index in range(0, len(encoded), 2))


def derive_input_obligations(program: dict) -> list[str]:
    """Return every key/button/Unicode unit that may need compensating release.

    The set is intentionally based on all input operations, including explicit
    UPs: a producer can be interrupted after native acceptance and before its
    local ledger commits the matching transition.
    """
    if type(program) is not dict or type(program.get("ops")) is not list:
        raise ValueError("program operations must be a list")
    obligations = set()
    current_target = None
    for index, operation in enumerate(program["ops"]):
        if type(operation) is not dict:
            raise ValueError(f"operation {index} must be an object")
        kind = operation.get("op")
        if kind in ("focus", "activate"):
            target = operation.get("target")
            if type(target) is not str or not target:
                raise ValueError(f"operation {index} target is required")
            current_target = target
        elif kind in ("key_chord", "key_state", "pointer_button"):
            if type(current_target) is not str or not current_target:
                raise ValueError(f"operation {index} requires a focused target")
            if kind == "key_chord":
                keys = operation.get("keys")
                if type(keys) is not list or any(type(key) is not str or not key
                                                  for key in keys):
                    raise ValueError(f"operation {index} keys must be nonempty strings")
                obligations.update(f"key:{current_target}:{key}" for key in keys)
            elif kind == "key_state":
                key = operation.get("key")
                if type(key) is not str or not key:
                    raise ValueError(f"operation {index} key must be a nonempty string")
                obligations.add(f"key:{current_target}:{key}")
            else:
                button = operation.get("button")
                if type(button) is not str or not button:
                    raise ValueError(f"operation {index} button must be a nonempty string")
                obligations.add(f"button:{current_target}:{button}")
        elif kind == "text":
            value = operation.get("text")
            if type(value) is not str:
                raise ValueError(f"operation {index} text must be a string")
            obligations.update(f"unicode:{unit:04X}" for unit in _utf16_units(value))
    return sorted(obligations)
