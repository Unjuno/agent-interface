"""Strictly parse one model-authored local displacement postcondition."""
import json

from local_displacement_postcondition_v1 import FIELDS


def parse(text):
    if not isinstance(text, str) or len(text.encode("utf-8")) > 4096:
        raise ValueError("bounded UTF-8 model output required")
    value = json.loads(text)
    if type(value) is not dict or set(value) != FIELDS:
        raise ValueError("exact postcondition object required")
    return value
