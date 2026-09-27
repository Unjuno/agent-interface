#!/usr/bin/env python3
"""Reverse only Python-Xlib's String8 text representation; leave bytes unchanged."""


def normalize(payload: str | bytes) -> bytes:
    if isinstance(payload, str):
        return payload.encode("UTF-8")
    if isinstance(payload, bytes):
        return payload
    return bytes(payload)
